import os
import re
import threading
import time
import unicodedata
from datetime import datetime, timedelta
from time import gmtime, strftime
from typing import Optional
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

TODAY = datetime.today().date() 

request_delay = 5

VIETNAMESE_PATTERN = {
    "[àáảãạăắằẵặẳâầấậẫẩ]": "a",
    "[ÀÁẢÃẠĂẮẰẴẶẲÂẦẤẬẪẨ]": "A",
    "[đ]": "d",
    "[Đ]": "D",
    "[èéẻẽẹêềếểễệ]": "e",
    "[ÈÉẺẼẸÊỀẾỂỄỆ]": "E",
    "[ìíỉĩị]": "i",
    "[ÌÍỈĨỊ]": "I",
    "[òóỏõọôồốổỗộơờớởỡợ]": "o",
    "[ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ]": "O",
    "[ùúủũụưừứửữự]": "u",
    "[ÙÚỦŨỤƯỪỨỬỮỰ]": "U",
    "[ỳýỷỹỵ]": "y",
    "[ỲÝỶỸỴ]": "Y",
}


def convert_accented_vietnamese_text(text) -> str:
    if type(text) != str:
        text = str(text)
    text = text.lower()
    text = unicodedata.normalize("NFC", text)
    for regex, replace in VIETNAMESE_PATTERN.items():
        text = re.sub(regex, replace, text)

    text = text.replace("\n", " ")
    return text


class JobGlintsCounting(object):
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.domain_url = "https://glints.com/vn/opportunities/jobs/explore?country=VN&"
        self.urls_code = [
            "searchCity=132294&locationName=Ho+Chi+Minh+City%2C+Vietnam",
            "searchCity=132462&locationName=H%C3%A0+N%E1%BB%99i%2C+Vietnam",
            "&searchCity=132500&locationName=Da+Nang%2C+Vietnam"
        ]
        self.week_code = "&lastUpdated=PAST_WEEK"
        pass

    def glints_count(self):
        global df_temp
        j = 0
        j_7 = 0

        companies_list = []
        for url_code in self.urls_code:
            url = self.domain_url+url_code
            self.driver.get(url)
            time.sleep(7)
            html_text = self.driver.page_source
            soup = BeautifulSoup(html_text, "html.parser")
            text = soup.select(
                "h1", class_="ExploreTabsc__JobCount-gs9c0s-4 dNOFLk")[0]
            job_number = int(re.findall(">(\d.*) việc", str(text))[0].strip())
            j += job_number

            page_numbers = int(job_number/30)+2
            for page_number in tqdm(range(page_numbers)):
                self.driver.get(url + f"&page={page_number}")
                time.sleep(3)
                html_text = self.driver.page_source
                all_jobs = html_text.split('aria-label="Job card')[1:]
                for job in all_jobs:
                    company = re.findall('alt="(.*)" size', job)
                    if len(company) > 0:
                        text = company[0].strip()
                        text = convert_accented_vietnamese_text(text)
                        if text not in companies_list:
                            companies_list.append(text)
        c = len(companies_list)

        companies_list = []
        for url_code in self.urls_code:
            url = self.domain_url+url_code+self.week_code
            self.driver.get(url)
            time.sleep(3)
            html_text = self.driver.page_source
            soup = BeautifulSoup(html_text, "html.parser")
            text = soup.select(
                "h1", class_="ExploreTabsc__JobCount-gs9c0s-4 dNOFLk")[0]
            job_number = int(re.findall(">(\d.*) việc", str(text))[0].strip())
            j_7 += job_number

            page_numbers = int(job_number/30)+2
            for page_number in tqdm(range(page_numbers)):
                self.driver.get(url + f"&page={page_number}")
                time.sleep(3)
                html_text = self.driver.page_source
                all_jobs = html_text.split('aria-label="Job card')[1:]
                for job in all_jobs:
                    company = re.findall('alt="(.*)" size', job)
                    if len(company) > 0:
                        text = company[0].strip()
                        text = convert_accented_vietnamese_text(text)
                        if text not in companies_list:
                            companies_list.append(text)
        c_7 = len(companies_list)
        self.driver.close()
        df_temp.iloc[0] = ["Glints", j, j_7, c, c_7, TODAY, 0, str(TODAY)]


class JobLinkedInCounting(object):
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        pass

    def linkedin_login(self):
        USER = "nickaohocpython@gmail.com"
        PWD = "nickao111"
        self.driver.get(
            "https://www.linkedin.com/uas/login?trk=guest_homepage-basic_nav-header-signin")
        time.sleep(7)
        # username
        username = self.driver.find_element_by_id("username")
        username.send_keys(USER)
        time.sleep(7)
        password = self.driver.find_element_by_id("password")
        password.send_keys(PWD)
        time.sleep(7)
        sign_in_button = self.driver.find_element_by_xpath(
            '//*[@type="submit"]')
        sign_in_button.click()

    def get_info(self, url):
        try:
            self.driver.get(url)
            time.sleep(7)
        except Exception as e:
            print(url)
        element = self.driver.find_elements_by_class_name(
        "jobs-search-results-list__text")
        result = element[1].text
        result = int(re.findall("(.*) results", result)[0].replace(",", ""))
        return result

    def count_linkedin(self):
        global df_temp
        self.linkedin_login()
        jobs_url_all = [
            "https://www.linkedin.com/jobs/search/?geoId=90010187&location=Ho%20Chi%20Minh%20City%20Metropolitan%20Area",
            "https://www.linkedin.com/jobs/search/?geoId=90010186&location=Hanoi%20Capital%20Region",
            "https://www.linkedin.com/jobs/search/?geoId=90010189&location=Da%20Nang%20Metropolitan%20Area"
        ]
        jobs_url_7 = [
            "https://www.linkedin.com/jobs/search/?f_TPR=r604800&geoId=90010187&location=Ho%20Chi%20Minh%20City%20Metropolitan%20Area",
            "https://www.linkedin.com/jobs/search/?f_TPR=r604800&geoId=90010186&location=Hanoi%20Capital%20Region",
            "https://www.linkedin.com/jobs/search/?f_TPR=r604800&geoId=90010189&location=Da%20Nang%20Metropolitan%20Area"
        ]

        j = 0
        j_7 = 0

        for domain_url in jobs_url_all:
            job_number = self.get_info(domain_url)
            j += job_number

        for domain_url in jobs_url_7:
            job_number = self.get_info(domain_url)
            j_7 += job_number

        c = None
        c_7 = None
        self.driver.close()
        df_temp.iloc[1] = ["LinkedIn", j, j_7, c, c_7, TODAY, 0, str(TODAY)]


class JobTopCVCounting(object):
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        pass

    @staticmethod
    def check_update(update):
        if "ngày" in update:
            if int(re.findall("\d+", update)[0]) > 14:
                return False
            else:
                return True
        elif "tuần" in update and int(re.findall("\d+", update)[0]) < 2:
            return True
        elif "tháng" in update or "năm" in update:
            return False
        else:
            return True

    def get_info(self, url):
        try:
            self.driver.get(url)
            time.sleep(3)
        except Exception as e:
            print(e.message)
        element = self.driver.find_elements_by_class_name(
            "jobs-search-results-list__title-heading")
        result = element[0].text
        result = int(re.findall("\n(.*) results", result)[0].replace(",", ""))
        return result

    def count_topcv(self):
        global df_temp
        company_list = []
        company_list_7 = []
        j = 0
        j_7 = 0

        location_codes = ["ha-noi-l1", "ho-chi-minh-l2", "da-nang-l8"]
        for location in location_codes:
            domain_url = f"https://www.topcv.vn/tim-viec-lam-moi-nhat-tai-{location}?salary=0&exp=0&sort=up_top"
            self.driver.get(domain_url)
            time.sleep(0.5)
            html_text = self.driver.page_source
            soup = BeautifulSoup(html_text, "html.parser")
            text = [str(i) for i in soup.select(
                "b", class_="text-highlight") if "text-highlight" in str(i)][0]
            text = text.split(">")[1].replace("</b", "").replace(",", "")
            job_numbers = int(text)
            j += job_numbers

            page_numbers = min(int(job_numbers/25)+1, 400)
            for number in tqdm(range(1, page_numbers+1)):
                url = domain_url + f"&page={number}"
                self.driver.get(url)
                time.sleep(0.5)

                html_text = self.driver.page_source
                soup = BeautifulSoup(html_text, "html.parser")
                soup.find_all(
                    "div", "job-item  bg-highlight  job-ta result-job-hover")
                jobs_list = self.driver.find_elements_by_class_name("job-item")
                for job in jobs_list:
                    infos = job.text.split("\n")
                    company = infos[1].strip()
                    company = convert_accented_vietnamese_text(company)
                    update = infos[-1].split("Cập nhật")[-1].strip()
                    if self.check_update(update):
                        j_7 += 1
                        company_list_7.append(company)
                    company_list.append(company)
            c = len(set(company_list))
            c_7 = len(set(company_list_7))
        self.driver.close()
        df_temp.iloc[2] = ['TopCV', j, j_7, c, c_7, TODAY, 0, str(TODAY)]


class JobVnwCounting(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_jobs(location: str):
        data = """{"query":"","filter":[{"field":"workingLocations.cityId","value":""" + \
            '"' + location + '"' + \
            """}],"ranges":[],"order":[],"hitsPerPage":200,"page":0}"""
        headers = {
            "accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Length": "256",
            "content-type": "application/json",
            "Host": "ms.vietnamworks.com",
            "Origin": "https://www.vietnamworks.com",
            "Referer": "https://www.vietnamworks.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        }
        url = "https://ms.vietnamworks.com/job-search/v1.0/search"
        res = requests.post(url, data, headers=headers).json()
        if res["meta"]["nbPages"] > 1:
            data = """{"query":"","filter":[{"field":"workingLocations.cityId","value":""" + '"' + location + '"' + \
                """}],"ranges":[],"order":[],"hitsPerPage":""" + \
                str(200*(res["meta"]["nbPages"]-1)) + ""","page":0}"""
            res = requests.post(url, data, headers=headers).json()
        return res

    def VNW_infor(self, location):
        GOAL_DATE = datetime.today().date() - timedelta(days=7)
        jobs = self.get_jobs(location)
        companies = [jobs["data"][i]["companyId"]
                     for i in range(len(jobs["data"]))]
        all_company = len(set(companies))
        all_job = jobs["meta"]['nbHits']
        last_updates = [datetime.strptime(
            jobs["data"][i]["lastUpdatedOn"][:10], '%Y-%m-%d').date() for i in range(len(jobs["data"]))]
        companies_7 = []
        job_7 = 0
        for job, update in tqdm(zip(jobs["data"], last_updates)):
            if update >= GOAL_DATE:
                job_7 += 1
                companies_7.append(job["companyId"])
        company_7 = len(set(companies_7))
        return all_job, job_7, all_company, company_7

    def count_vnw(self):
        global df_temp
        locations = ['ha-noi', 'ho-chi-minh', 'da-nang']
        locations_encoded = dict(zip(locations, ["24", "29", "17"]))

        result = [0, 0, 0, 0]
        for location in locations:
            location = locations_encoded[location]
            result += np.array(self.VNW_infor(location))
        all_job, job_7, all_company, company_7 = result
        df_temp.iloc[3] = ['Vietnamwork', all_job,
                           job_7, all_company, company_7, TODAY, 0, str(TODAY)]


class JobCbCounting(object):
    def generate_url_cb(self):
        jobs, jobs_7_days = self.count_jobs()
        max_page_jobs, max_pages_7_jobs = int(jobs/50)+2, int(jobs_7_days/50)+2
        for index in range(1, max_page_jobs):
            job_page = f'https://careerbuilder.vn/viec-lam/ha-noi-ho-chi-minh-da-nang-l4,8,511-trang-{index}-vi.html'
            f_jobs_pages = open(os.path.join(
                "careerbuilder_data", "jobs_pages.txt"), "a")
            f_jobs_pages.write(job_page+"\n")
            f_jobs_pages.close()
            if index > max_pages_7_jobs:
                continue
            job_page_7 = f'https://careerbuilder.vn/viec-lam/ha-noi-ho-chi-minh-da-nang-l4,8,511d7-trang-{index}-vi.html'
            f_jobs_pages = open(os.path.join(
                "careerbuilder_data", "jobs_pages.txt"), "a")
            f_jobs_pages.write(job_page_7+"\n")
            f_jobs_pages.close()
        time.sleep(3)
        return jobs, jobs_7_days

    def count_jobs(self):
        os.system("scrapy crawl jobs_counts")
        time.sleep(3)
        f = open(os.path.join("careerbuilder_data", "job_list.txt"), "r")
        lines = [i.replace("\n", "") for i in f.readlines()]
        jobs = int(lines[0])
        jobs_7_days = int(lines[1])
        f.close()
        os.remove(os.path.join("careerbuilder_data", "job_list.txt"))
        return jobs, jobs_7_days

    def count_companies(self):
        global df_temp
        jobs, jobs_7_days = self.generate_url_cb()
        os.system("scrapy crawl full_careerbuilder")
        f = open(os.path.join("careerbuilder_data", "company_list.txt"), "r")
        companies = []
        companies_7 = []
        lines = [i.replace("\n", "") for i in f.readlines()]
        day_7_flag = False
        for line in lines:
            if "7 days" in line:
                day_7_flag = True
                continue
            if day_7_flag:
                day_7_flag = False
                companies_7.append(line)
            else:
                companies.append(line)
        f.close()
        os.remove(os.path.join("careerbuilder_data", "company_list.txt"))
        os.remove(os.path.join("careerbuilder_data", "jobs_pages.txt"))
        df_temp.iloc[4] = ["Careerbuilder", jobs, jobs_7_days, len(set(companies)),
                           len(set(companies_7)), TODAY, 0, str(TODAY)]


class JobItviecCounting(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_data(location_encode: str, page_number: Optional[int] = 0):
        data = f"""page={page_number}&query=&source=search_job"""
        headers = {
            "accept": "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "cookie": "_gcl_au=1.1.2681873.1644799971; G_ENABLED_IDPS=google; _fbp=fb.1.1644799971891.293608402; _gid=GA1.2.177588134.1645018623; last_city_searched=ho-chi-minh-hcm; viewed_jobs=05-devops-engineers-linux-database-ngan-hang-tmcp-tien-phong-tpbank-4839%7Chan-net-developer-up-to-160-hybrid-technologies-2700%7Cnet-developer-c-sql-global-insurance-corporation-4732%7Cfrontend-developer-up-to-15m-vision-network-viet-nam-2335%7Cbackend-developer-java-php-mysql-sbigtech-viet-nam-0218%7Cjava-solution-architect-tech-lead-sai-digital-2053; _dc_gtm_UA-42033311-2=1; _gat_UA-42033311-1=1; _ga_4Y048XFC1T=GS1.1.1645110219.8.1.1645110231.0; _ga_S6FMJYVBJ2=GS1.1.1645110219.8.1.1645110231.0; _ga=GA1.2.1597218388.1644799971; _ITViec_session=0C25Lyl7v99W4HKGf8rpolwU1GhirfZ02qV%2BJX0d9HPZxZOSZ5iUa%2F%2FcZUxWdj44TlkPfy5weDNISc9PtjpuH1fO6ZS1gxpyzndFI8s7zUElwkbeWvvE00lP9iALl5du85xSHxbvjZZk6KVImPx4HxE71x%2FkIiNubX2tmAAENNBEuBiBnYm1mOHskYYPadnbVSwXA4Yb68NmEIHE3XGTh2UN%2B8UzIv3KgtLVYVO2OE5cn8dzPsLPZx2HusyEf1RI85wA0h63QZqnv%2F%2FACSz%2F12CsPC6b8AEP%2FhtO63m2iqQvAnW8sHbAfyN7PEgSqcEB2%2Fc9neVjFVHJI7WtAZjh--e%2FuAWeFcWM%2FGM1l0--8%2FFZSTT8Klk8sr8f4tPecw%3D%3D",
            "referer": f"https://itviec.com/it-jobs/{location_encode}",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "x-csrf-token": "wEUdvyNXM7ZtbLwyFB63kgCMezDwThNVq8kQKmyVCOjNtjVQEDsCJ-6T02c7k4oiru58mf9vxYynTKcYWK0Drw",
            "x-requested-with": "XMLHttpRequest",
        }
        url = f"https://itviec.com/it-jobs/{location_encode}"
        res = requests.get(url, data, headers=headers).json()
        return res

    def count_jobs(self, location_encode: str):
        data = self.get_data(location_encode)
        jobs_number = int(
            re.match("\d+", data['headline_result_html'].replace(",", "")).group(0))
        return jobs_number

    def count_others(self, jobs_number: int, location_encode: str):
        pages_number = int(jobs_number/20)+2
        jobs_number_7 = 0
        companies_number = []
        companies_number_7 = []
        for page_number in tqdm(range(pages_number+1)):
            data = self.get_data(location_encode, page_number)
            if not data['jobs_html'].strip():
                break
            data2 = data["jobs_html"].split(
                "<div class=\'job_content\'>\n<div class=\'logo\'>")[1:]
            for text in data2:
                company_name = re.findall(
                    "alt=\'(.*)\' data-controller=", text)
                if company_name not in companies_number:
                    companies_number.append(company_name)
                update_time = re.findall(
                    "class=\'distance-time\'>\n(.*)\n", text)
                if not update_time:
                    try:
                        update_time = re.findall(
                            "class=\'distance-time highlight\'>\n(.*)\n", text)
                    except:
                        print(text)
                        break
                update_time = update_time[0]
                if update_time[-1] == "h" or (update_time[-1] == "d" and int(update_time[:-1]) < 8):
                    jobs_number_7 += 1
                    if company_name not in companies_number_7:
                        companies_number_7.append(company_name)
        return jobs_number_7, len(companies_number), len(companies_number_7)

    def count_itviec(self):
        global df_temp
        location_encodes = ['ho-chi-minh-hcm', 'da-nang', 'ha-noi']
        j = 0
        j_7 = 0
        c = 0
        c_7 = 0
        for location_encode in location_encodes:
            jobs = self.count_jobs(location_encode)
            jobs_7, companies, companies_7 = self.count_others(
                jobs, location_encode)
            j += jobs
            j_7 += jobs_7
            c += companies
            c_7 += companies_7
        df_temp.iloc[5] = ['Itviec', j, j_7, c, c_7, TODAY, 0, str(TODAY)]


class JobTopDevCounting(object):
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        pass

    def top_dev_jobs(self, page_num):

        csrf_token = self.driver.find_elements(
            by=By.CSS_SELECTOR, value='meta[name="csrf-token"]')[0].get_attribute('content')
        body_dict = {
            'q': '',
            'cid': '',
            'level': '',
            'jtype': '',
            'min': '',
            'max': '',
            'lastpage': 50-page_num+1,
            'page': page_num,
            'company': '',
            'sk': '',
            'other': '',
            'hackerrank': '',
            'province_id': '',
            'keyword_str': '',
            'skill_str': '',
            '_token': csrf_token,
            'locale': 'en',
            'keyword_meta': '',
            'next_scroll_page': page_num
        }
        script = f"""
            return fetch(
                'https://topdev.vn/it-jobs/scroll-data',
                {{
                    method: 'POST',
                    body: new URLSearchParams('{urlencode(body_dict)}'),
                    headers: {{'x-requested-with': 'XMLHttpRequest'}}
                }}
            ).then(res => res.text());
        """
        self.driver.switch_to.default_content()
        time.sleep(request_delay)
        results = self.driver.execute_script(script)
        time.sleep(request_delay)

        soup = BeautifulSoup(results, 'html.parser')
        company = soup.find_all('p', class_='job-location fl mb-1')
        company_list = []
        for j in company:
            if "fa fa-map-marker" in str(j) or "fa fa-cog" in str(j):
                continue
            else:
                company_list.append(j.text.strip().encode(
                    "ascii", "ignore").decode("ascii"))
        job_time_list = []
        job_time = soup.find_all('p', class_='job-ago')
        for t in job_time:
            job_time_list.append(t.text.strip())
        elms = soup.select('a.job-title')
        job_links = [elm.get('href') for elm in elms]

        df = pd.DataFrame(
            {'link_job': job_links, 'company_name': company_list, 'time': job_time_list})
        return df


    def top_dev_crawling(self):
        global df_temp
        urls = {'Ho Chi Minh': 'https://topdev.vn/viec-lam-it/ho-chi-minh-kl79',
                'Ha Noi': 'https://topdev.vn/viec-lam-it/ha-noi-kl01', 'Da Nang': 'https://topdev.vn/viec-lam-it/da-nang-kl48'}
        top_dev = []
        for key, value in tqdm(urls.items()):

            self.driver.get(value)
            page = 0
            result = []
            while True:
                page += 1
                df = self.top_dev_jobs(page)
                if df.shape[0] == 0:
                    break

                df['location'] = key
                result.append(df)
            final_df = pd.concat(result)
            top_dev.append(final_df)

        top_dev_df = pd.concat(top_dev)

        j = [top_dev_df['link_job'].nunique()][0]
        j_7 = [top_dev_df[top_dev_df['time'].str.contains('(?:hour|minute|day|hour|second)', regex=True)]['link_job'].nunique()][0]
        c = [top_dev_df['company_name'].nunique()][0]
        c_7 = [top_dev_df[top_dev_df['time'].str.contains('(?:hour|minute|day|hour|second)', regex=True)]['company_name'].nunique()][0]
        self.driver.close()
        df_temp.iloc[6] = ["TopDev", j, j_7, c, c_7, TODAY, 0, str(TODAY)]

class JobITnaviCounting(object):
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        pass

    def itnavi_jobs(self, page_num, link):
        url = link + f'''?page={page_num}'''
        self.driver.switch_to.default_content()
        time.sleep(request_delay)
        self.driver.get(url)
        results = self.driver.page_source
        time.sleep(request_delay)

        soup = BeautifulSoup(results, 'html.parser')
        id = soup.find_all('div', class_='jsl-item jsl_item') + \
            soup.find_all('div', class_='jsl-item jsl_item active')
        id_list = []
        for i in id:
            id_list.append(i['data-id'])

        company_list = []
        company = soup.find_all('p', class_="jsl-item__cpn")
        for i in company:
            company_list.append(i.text.strip())
        job_time_list = []
        job_time = soup.find_all('p', class_='jsl-item__sm')
        for t in job_time:
            job_time_list.append(t.text.strip())
        df = pd.DataFrame(
            {'job_id': id_list, 'company_name': company_list, 'time': job_time_list})
        return df


    def itnavi_crawling(self):
        urls = {'Ho Chi Minh': 'https://itnavi.com.vn/job/ho-chi-minh',
                'Ha Noi': 'https://itnavi.com.vn/job/ha-noi', 'Da Nang': 'https://itnavi.com.vn/job/da-nang'}
        itnavi = []
        for key, value in tqdm(urls.items()):

            page = 0
            result = []
            while True:
                page += 1
                df = self.itnavi_jobs(page, value)
                if df.shape[0] == 0:
                    break
                df['location'] = key
                result.append(df)
            final_df = pd.concat(result)
            itnavi.append(final_df)
        itnavi_df = pd.concat(itnavi)
        j = [itnavi_df['job_id'].nunique()][0]
        j_7 = [itnavi_df[itnavi_df['time'].isin(['0 d', '1 d', '2 d', '3 d', '4 d', '5 d', '6 d'])]['job_id'].nunique()][0]
        c = [itnavi_df['company_name'].nunique()][0]
        c_7 = [itnavi_df[itnavi_df['time'].isin(['0 d', '1 d', '2 d', '3 d', '4 d', '5 d', '6 d'])]['company_name'].nunique()][0]

        df_temp.iloc[7] = ["ITNavi", j, j_7, c, c_7, TODAY, 0, str(TODAY)]
        self.driver.close()
        return result


if __name__ == "__main__":
    current_path = "careerbuilder"
    os.chdir(current_path)
    df_temp = pd.DataFrame(columns=['source', 'all_jobs', 'jobs_posted_in_7_days', 'companies',
                                    'companies_posted_jobs_in_7_days', 'updated_date', 'last_update', 'string_date'], index=range(8))

    Job_Vnw_Counting = JobVnwCounting()
    Job_Itviec_Counting = JobItviecCounting()
    Job_CB = JobCbCounting()
    Job_Topcv = JobTopCVCounting()
    Job_Linkedin = JobLinkedInCounting()
    Job_Glints = JobGlintsCounting()
    Job_Itnavi = JobITnaviCounting()
    Job_Topdev = JobTopDevCounting()

    t1 = threading.Thread(target=Job_Vnw_Counting.count_vnw)
    t2 = threading.Thread(target=Job_Itviec_Counting.count_itviec)
    t3 = threading.Thread(target=Job_CB.count_companies)
    t4 = threading.Thread(target=Job_Topcv.count_topcv)
    t5 = threading.Thread(target=Job_Linkedin.count_linkedin)
    t6 = threading.Thread(target=Job_Glints.glints_count)
    t7 = threading.Thread(target=Job_Topdev.top_dev_crawling)
    t8 = threading.Thread(target=Job_Itnavi.itnavi_crawling)


    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t7.start()
    t8.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    t7.join()
    t8.join()

    os.chdir("Results")

    if not os.path.exists("company_job_counts.csv"):
        df = pd.DataFrame()
    else:
        df = pd.read_csv("company_job_counts.csv")
    df.to_csv("old_dateframe.csv", index=False)

    new_last_update = df[df["string_date"]
                         == str(TODAY)]["last_update"].values
    df.loc[df["string_date"] == str(
        TODAY), "last_update"] = new_last_update + [1]*len(new_last_update)

    df_temp["last_update"] = [1]*len(df_temp)
    df_temp["updated_date"] = [datetime.now()]*len(df_temp)
    df_temp = df_temp.dropna(axis=1, how='all')
    df = pd.concat([df, df_temp])
    df.to_csv("company_job_counts.csv", index=False)
    df_temp.to_csv("today.csv", index=False)

    df_temp = pd.read_csv("today.csv")
    df_temp["updated_date"] = pd.to_datetime(df_temp["updated_date"], format='%Y-%m-%d %H:%M:%S')

    project_name = 'able-keep-311204'
    dataset_name = 'company_job_counts'
    table_name = "company_job_counts"
    schema = [
        {'name': 'source', 'type': 'STRING'},
        {'name': 'all_jobs', 'type': 'INTEGER'},
        {'name': 'jobs_posted_in_7_days', 'type': 'INTEGER'},
        {'name': 'all_companies', 'type': 'INTEGER'},
        {'name': 'companies_posted_jobs_in_7_days', 'type': 'INTEGER'},
        {'name': 'updated_date', 'type': 'TIMESTAMP'},
        {'name': 'last_update', 'type': 'INTEGER'},
        {'name': 'string_date', 'type': 'STRING'}
    ]
    pd.io.gbq.to_gbq(df_temp, destination_table='{}.{}'.format(
        dataset_name, table_name), project_id=project_name, table_schema=schema, if_exists='append')