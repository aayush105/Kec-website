import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import FetchedData,ResultData,Subscriber
from datetime import datetime
import pdf2image
import pytesseract
import re
from kecWebsite.settings import ocr_config
from django.core.mail import send_mail, send_mass_mail
from kecWebsite import settings
from django.db.utils import IntegrityError


class TeamMember:
    def __init__(self, name, title, bio, email=None,profile_image=None,phone=None):
        self.name = name
        self.title = title
        self.bio = bio
        self.profile_image = profile_image
        self.phone = phone
        self.email = email


faculties = ["BCT","BEX","BCE"]

def fetchData():
    print("-----------------CHECKING FOR THE UPDATED DATA IN IOE-------------------------")
    for page in range(1, 10):
        response = requests.get('https://exam.ioe.edu.np/?page=' + str(page), timeout=60)
        soup = BeautifulSoup(response.text, 'html.parser')
        dates = soup.select("#datatable > tbody:nth-child(2) > tr > td:nth-child(3)")
        tabled = soup.select("#datatable > tbody:nth-child(2) > tr")
        for row, date in zip(tabled, dates):
            link = row.a
            notice_title = row.span
            if ('Notice' in str(notice_title) or 'Result' in str(notice_title)) and 'BE' in str(notice_title):
                text = row.span.text
                href = row.a.get('href')
                href = href.replace(' ', '%20')
                url = urljoin('https://exam.ioe.edu.np/', href)
                name = text.replace('/', '').replace('(', '').replace(')', '').replace(',', '').replace(':', '')
                if 'Notice' in str(notice_title):
                    category = 'notice'
                    filename = f'Notice {name}.pdf'
                    folder = 'notice'
                else:
                    category = 'result'
                    filename = f'Result {name}.pdf'
                    folder = 'result'

                # Check if the notice/result with the same URL already exists
                if FetchedData.objects.filter(url=url).exists():
                    print(f'{filename} already exists in the database.')
                    continue
                
                
                # Download and save the PDF file
                file_dir = os.path.join('fetched_data', folder)
                os.makedirs(file_dir,exist_ok=True)
                
                file_path = os.path.join(file_dir,url.split("/")[-1])
                date_text = date.text.replace(',','')
                date_obj = datetime.strptime(date_text, "%A %B %d %Y")

                try:
                    response = requests.get(url, timeout=60)
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    is_downloaded = True
                except Exception as exception:
                    print(f'Failed to download {filename}: {str(exception)}')
                    is_downloaded = False

                try:
                    fetched_data = FetchedData(title=text, date=date_obj.date(), category=category, file_path=os.path.join(folder,url.split("/")[-1]), url=url, is_downloaded=is_downloaded, is_ocr_read=False)
                    fetched_data.save()
                except IntegrityError:
                    print(f'{filename} already exists in the database.')
    readResult()


def retryDownload():
    print('Retrying downloads...')
    not_downloaded = FetchedData.objects.filter(is_downloaded=False)
    for data in not_downloaded:
        try:
            response = requests.get(data.url, timeout=60)
            with open(os.path.join("fetched_data",data.file_path.name), 'wb') as f:
                f.write(response.content)
            data.is_downloaded = True
            data.save()
            print(f'Successfully downloaded {data.title}')
        except Exception as e:
            print(f'Failed to download {data.title}: {str(e)}')


def readResult():

    unmarked_files = FetchedData.objects.filter(category="result",is_ocr_read=False,is_downloaded=True)
    print("----------------------READING---------------------------")
    for file in unmarked_files:
        if "Re-totalling" in file.title:
            continue
        pdf_file = os.path.join("fetched_data",file.file_path.name)
        print(pdf_file)

        bs_pattern = r'2?\d+'
        bs_matches = re.findall(bs_pattern,file.title)
        bs = bs_matches[-1] if bs_matches[0][0] == "2" else "2"+bs_matches[-1]

        images = pdf2image.convert_from_path(pdf_file)
        
        faculty_level_pattern = r'(I|II|III|IV)/\s*(I|II|III|IV)\s+'
        raw_text = pytesseract.image_to_string(images[0])
        raw_text = raw_text.split("Page")[0].replace("l","I")
        year_part = re.findall(faculty_level_pattern,raw_text)
        try:
            year = year_part[0][0]
            part = year_part[0][1]
        except IndexError:
            continue

        final_text = []
        for pg_no,image in enumerate(images):
            if pg_no == 0:
                text = pytesseract.image_to_string(image,config=ocr_config)
                text = text.split("।")[-1].strip()
            elif pg_no < len(images)-1:
                text = pytesseract.image_to_string(image,config="--psm 6")
                text = text.split("Nepal")[-1].strip()
            else:
                text = pytesseract.image_to_string(image,config=ocr_config)
                text = text.split("Nepal")[-1].strip()
                text = "".join(text.split("परीक्षा")[0]).strip()

            final_text.append(text.strip().replace(" &",",").replace(".",""))
        

        input_txt = "".join(final_text)
        # Define the regular expression pattern to match the faculty names and their symbol numbers
        symbol_dict = {}
        pattern = r'(\w+)\s+(\w+/?\w*)\s+((?:\d+(?:,\s*)?)+)'
        for match in re.finditer(pattern, input_txt):
            faculty_name = match.group(1)
            faculty_level = match.group(2)
            # symbol_numbers = [int(x) for x in match.group(3).split(',')]
            symbol_numbers = re.findall(r'\b\d+\b',match.group(3))
            key = faculty_name
            symbol_dict[key] = symbol_numbers



        for faculty in faculties:
            if faculty in symbol_dict.keys():
                for symbol in symbol_dict[faculty]:
                    try:
                        result_data = ResultData.objects.create(faculty=faculty,year=year,part=part,symbol=symbol,bs=bs)
                        checkSubscriberAndNotify(result_data)
                    except IntegrityError:
                        continue
                
                failed_subscribers = Subscriber.objects.filter(bs_year=bs_matches[-1],faculty=faculty,year=year,part=part, is_active=True)
                failed_messages = []
                for subscriber in failed_subscribers:
                    subject = 'We are sorry, you have not passed the exam'
                    message = f'Hi {subscriber.fullname},\n\n' \
                            f'We regret to inform you that you have not passed the exam. ' \
                            f'Please contact us for more information.\n\n' \
                            f'Thank you,\n' \
                            f'The KEC Team'
                    failed_messages.append((subject, message, settings.EMAIL_HOST_USER, [subscriber.email]))

                if failed_messages:
                    send_mass_mail(failed_messages)
                    failed_subscribers.delete()
    
       
        file.is_ocr_read = True
        file.save()
    
    


def checkSubscriberAndNotify(result_data):
    subscriber = Subscriber.objects.filter(symbol=result_data.symbol, faculty=result_data.faculty,year=result_data.year,bs_year=result_data.bs,is_active=True).first()
    if subscriber:
        message = f"Congratulations, {subscriber.fullname}, you have passed the exam."
        send_mail(
            subject="Exam Result",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[subscriber.email],
        )
        
        subscriber.delete()


         

    