import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import FetchedData,ResultData
from datetime import datetime
import pdf2image
import pytesseract
import re
from kecWebsite.settings import ocr_config

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
                response = requests.get(url)
                file_dir = os.path.join('fetched_data', folder)
                os.makedirs(file_dir,exist_ok=True)
                file_path = os.path.join(file_dir,filename)
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                date_text = date.text.replace(',','')
                date_obj = datetime.strptime(date_text, "%A %B %d %Y")
                # print(text)
                fetched_data = FetchedData(title=text, date=date_obj.date(), category=category, file_path=os.path.join(folder,filename), url=url, is_ocr_read=False)
                fetched_data.save()
                # print(f'Downloaded {filename} and saved to the database.')


def readResult():
    faculties = ["BCT","BEX","BCE"]
    unmarked_files = FetchedData.objects.filter(category="result",is_ocr_read=False)
    print("----------------------READING---------------------------")
    for file in unmarked_files:
        if "Re-totalling" in file.file_path.name:
            continue
        pdf_file = os.path.join("fetched_data",file.file_path.name)
        print(pdf_file)
        images = pdf2image.convert_from_path(pdf_file)
        
        faculty_level_pattern = r'(I|II|III|IV)/\s*(I|II|III|IV)\s+'
        raw_text = pytesseract.image_to_string(images[0])
        raw_text = raw_text.split("Page")[0].replace("l","I")
        year_part = re.findall(faculty_level_pattern,raw_text)
        year = year_part[0][0]
        part = year_part[0][1]

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
        pattern = r'(\w+)\s+(\w+/?\w*)\s+((?:\d+(?:,\s*)?)+)'
        # Iterate over the matches in the input text and create a dictionary of faculty names and symbol numbers
        symbol_dict = {}
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
                    result_data = ResultData.objects.create(faculty=faculty,year=year,part=part,symbol=symbol)

    
        file.is_ocr_read = True
        file.save()