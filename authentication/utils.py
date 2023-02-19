import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import FetchedData
from datetime import datetime

def fetchData():
    print("-----------------CHECKING FOR THE UPDATED DATA IN IOE-------------------------")
    for page in range(1, 10):
        response = requests.get('https://exam.ioe.edu.np/?page=' + str(page), timeout=60)
        soup = BeautifulSoup(response.text, 'html.parser')
        dates = soup.select("#datatable > tbody:nth-child(2) > tr > td:nth-child(3)")
        tabled = soup.table.find_all('tr')[1:]
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
                    # print(f'{filename} already exists in the database.')
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
                fetched_data = FetchedData(title=text, date=date_obj.date(), category=category, file_path=os.path.join(folder,filename), url=url)
                fetched_data.save()
                # print(f'Downloaded {filename} and saved to the database.')
