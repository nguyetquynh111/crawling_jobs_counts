import codecs
import os
import re
import time

import numpy as np
import scrapy
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
}


class CareerBuilderSearch(scrapy.Spider):
    name = 'jobs_counts'
    allowed_domain = ["careerbuilder.vn"]
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "CONCURRENT_REQUESTS_PER_IP": 3,
        "DOWNLOAD_DELAY": 1,
    }

    def start_requests(self):
        urls = [
            "https://careerbuilder.vn/viec-lam/ha-noi-ho-chi-minh-da-nang-l4,8,511-vi.html",
            "https://careerbuilder.vn/viec-lam/ha-noi-ho-chi-minh-da-nang-l4,8,511d7-vi.html",
        ]
        for url in urls:
            time.sleep(np.random.randint(5, 10))
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                headers=HEADERS,
                callback=self.parse
            )

    def parse(self, response):
        with open(os.path.join(
                "careerbuilder_data", "job_list.txt"), "a") as job_list:
            filename = re.sub("\W", "", response.url) + ".html"
            with open(filename, 'wb') as f:
                f.write(response.body)
            f = codecs.open(filename, 'r')
            text = f.read()
            soup = BeautifulSoup(text, "lxml")
            result = soup.select(".job-found-amout p")[0].text
            result = result.replace(" việc làm", "").replace(",", "")
            job_list.write(result+"\n")
            job_list.close()
            os.remove(filename)
