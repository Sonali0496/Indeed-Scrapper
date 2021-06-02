from bs4 import BeautifulSoup
import requests
import time
from django.conf import settings
from indeed_jobs.models import Job


class IndeedScrapper(object):
    q_params = {
        'q': 'Big Data Engineer',
        'filter': 0,
        'start': 0
    }

    host = "https://ca.indeed.com/jobs"
    job_list = []
    total_results = 0
    current_page = 1

    def scrap_jobs(self, keyword=""):
        if keyword:
            self.q_params['q'] = keyword

        while True:
            success, res = self.get_response()
            if not success:
                print('ERR - stopping scraping.....')
                break
            if not res:
                continue
            self.parse_html(res)
            has_next = self.next_page()
            if not has_next:
                print('Scrapping done....stopping')
                break
            self.insert_db()
            time.sleep(settings.SCRAPPER_SLEEP_SEC)
        return

    def next_page(self):
        self.q_params['start'] += 10
        if self.q_params['start'] > self.total_results:
            return False
        return True

    def get_response(self):
        params = {}
        for key, value in self.q_params.items():
            if value:
                params[key] = value
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
            "referer": "https://ca.indeed.com/"
        }
        try:
            res = requests.get(self.host, params=params, headers=headers, timeout=15)
        except requests.Timeout:
            print('ERR [get_response] - timeour')
            return True, None
        if res.status_code == 200:
            return True, res.content
        else:
            print("ERR [get_response] - failed to get response, status code - ", res.status_code, res.content)
            return False, None

    def parse_html(self, html_res):
        _, res = self.get_response()
        if not res:
            print("empty res")
            return

        soup = BeautifulSoup(res, "html.parser")

        # get job count
        page = soup.find('div', attrs={'id': 'searchCountPages'}).get_text()
        print('On Page - ', page.strip())
        if not self.total_results:
            job_count = int(page.split("of")[1].split('j')[0].replace(',', ''))
            self.total_results = job_count

        # get list of jobs on a page
        jobs = soup.findAll(attrs={'class': 'jobsearch-SerpJobCard'})

        for job in jobs:
            # get title
            title = job.find('a', attrs={'data-tn-element': 'jobTitle'})

            # company name
            company = job.find('span', attrs={'class': 'company'})

            link = title.get('href')

            j = {
                'title': self.clean_text(title.get_text()),
                'company': self.clean_text(company.get_text()),
                'link': link,
                'keyword': self.q_params['q']
            }
            # location
            loc = job.find('span', attrs={'class': 'location'})
            if loc:
                loc = self.clean_text(loc.get_text())
                j['location'] = loc

                # ratings
            rating = job.find('span', attrs={'class': 'ratingsContent'})
            if rating:
                j['rating'] = float(self.clean_text(rating.get_text()))

            # salary
            salary = job.find('span', attrs={'class': 'salaryText'})
            if salary:
                j['salary'] = self.clean_text(salary.get_text())

            # summary
            summary = job.find('div', attrs={'class': 'summary'})
            # todo

            # date posted
            posted = job.find('span', attrs={'class': 'date'})
            # j['posted'] = posted.get_text()
            self.job_list.append(j)
        return

    def clean_text(self, text):
        cleaned_text = text.strip()
        # cleaned_text = re.sub('[^a-zA-Z0-9-_*. ]', '', text) if text else ''
        return cleaned_text

    def insert_db(self):
        print("inserting to db")
        for job in self.job_list:
            Job.objects.create(**job)

        self.job_list = []

