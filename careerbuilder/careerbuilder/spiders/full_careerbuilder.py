
import codecs
import os
import re
import time
import unicodedata

import numpy as np
import scrapy
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
}


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


class CareerBuilderSearch(scrapy.Spider):
    name = 'full_careerbuilder'
    allowed_domain = ["careerbuilder.vn"]
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CONCURRENT_REQUESTS_PER_IP": 1,
        "DOWNLOAD_DELAY": 3,
    }

    def start_requests(self):
        f_jobs_pages = open(os.path.join(
            "careerbuilder_data", "jobs_pages.txt"), "r")
        jobs_pages_urls = [i.replace("\n", "")
                           for i in f_jobs_pages.readlines()]
        f_jobs_pages.close()
        for url in tqdm(jobs_pages_urls):
            time.sleep(np.random.randint(5, 10))
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                headers=HEADERS,
                callback=self.parse
            )

    def parse(self, response):
        with open(os.path.join(
                "careerbuilder_data", "company_list.txt"), "a") as company_list:
            filename = re.sub("\W", "", response.url) + ".html"
            with open(filename, 'wb') as f:
                f.write(response.body)
            f = codecs.open(filename, 'r')
            text = f.read()
            soup = BeautifulSoup(text, "lxml")
            data_list = soup.find_all("a")
            for index, item in enumerate(data_list):
                if "job_link" in str(item):
                    company_data = data_list[index-1].get("title")
                    company_data = convert_accented_vietnamese_text(
                        company_data)
                    if "d7" in filename:
                        company_list.write("7 days" + "\n")
                    company_list.write(company_data+"\n")
            company_list.close()
            os.remove(filename)
