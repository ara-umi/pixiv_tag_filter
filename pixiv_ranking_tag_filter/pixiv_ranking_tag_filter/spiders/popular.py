import json
import os.path
import random
import re
import time

import scrapy
from scrapy import signals

input_url = input("""*******************************************************************************
First page url:""")

test_url = "https://www.pixiv.net/tags/%E9%A3%8E%E6%99%AF/illustrations?order=popular_d&scd=2022-08-03&ecd=2022-08-27&blt=100&bgt=299"


class PopularSpider(scrapy.Spider):
    name = "popular"
    allowed_domains = ["www.pixiv.net", "i.pximg.net"]
    start_url = input_url
    querystring_dict = {
        "s_mode": "s_tag_full",  # 全标签搜索
        "type": "illust_and_ugoira"  # 限制图片格式
    }
    ajax_url = None
    cookies_fp = "./cookies_vip.txt"
    start_page = 1
    now_page = start_page
    end_page = 50
    history_fp = f"./history/{name}.json"
    history = None

    random_sleep_time = 1

    custom_settings = {
        "ITEM_PIPELINES": {
            "pixiv_ranking_tag_filter.pipelines.PixivRankingTagFilterPipeline": 300,
        },
        "DOWNLOADER_MIDDLEWARES": {
            "pixiv_ranking_tag_filter.middlewares.PixivProxyMiddleware": 200,
            "pixiv_ranking_tag_filter.middlewares.PixivUserAgentMiddleware": 300,
            "pixiv_ranking_tag_filter.middlewares.PixivRefererMiddleware": 350,
        },
        "LOG_ENABLED": True,
        "LOG_ENCODING": "utf-8",
        "LOG_FILE": "./log/" + f"{name}_" + time.strftime("%Y.%m.%d.%H.%M.%S", time.localtime(time.time())) + ".log",
        "LOG_LEVEL": "INFO",
        "COOKIES_ENABLED": True
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwarg):
        self = cls(*args, **kwarg)
        crawler.signals.connect(self.start_spider, signal=signals.spider_opened)
        crawler.signals.connect(self.end_spider, signal=signals.spider_closed)
        return self

    def start_spider(self):
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}: Spider start")
        self.load_history()
        self.shape_into_ajax()

    def end_spider(self):
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}: Spider end")
        with open(self.history_fp, "w") as f:
            json.dump(list(self.history), f, indent=4)
        print(f"Dump history, total: {len(self.history)}")

    def load_history(self):
        if not os.path.exists(self.history_fp):
            self.history = set()
        else:
            with open(self.history_fp, "r") as f:
                self.history = set(json.load(f))
            print(f"Load history, total: {len(self.history)}")

    def shape_into_ajax(self) -> str:
        pattern_tag = re.compile(r"tags/(?P<tag>.+?)/")
        pattern_type = re.compile(r"/(?P<type>[\w]+?)\?")
        qs_tag = pattern_tag.search(self.start_url).group("tag")
        qs_type = pattern_type.search(self.start_url).group("type")
        tail = self.start_url.split("?")[-1]
        tail_li = tail.split("&")
        for param in tail_li:
            self.querystring_dict[param.split("=")[0]] = param.split("=")[-1]
        self.ajax_url = "https://www.pixiv.net/ajax/search"
        self.ajax_url += "/" + qs_type
        self.ajax_url += "/" + qs_tag
        self.ajax_url += "?" + "word=" + qs_tag
        # 以上是一定会有的，下面是选填的
        for key, value in self.querystring_dict.items():
            self.ajax_url += "&" + key + "=" + value

    def shape_page_url(self, page: int):
        return self.ajax_url + "&p=" + str(page)

    @staticmethod
    def random_sleep(s_time):
        time.sleep(random.uniform(0, s_time))

    def load_cookies(self) -> dict:
        with open(self.cookies_fp, "r") as f:
            cookies_str = f.read()
            cookies_li = cookies_str.split(";")
            cookies = {}
            for content in cookies_li:
                key = content.split("=")[0].strip(" ")
                value = content.split("=")[-1].strip(" ")
                cookies[key] = value
            return cookies

    def start_requests(self):
        start_url = self.shape_page_url(self.start_page)
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}: Start search page {self.now_page}")
        cookies = self.load_cookies()
        yield scrapy.Request(url=start_url, cookies=cookies, callback=self.parse_page)

    def parse_page(self, response, **kwargs):
        resp_json = response.json()
        error = resp_json.get("error")
        assert error != "false", f"Error occurred during spider on {response.url}"
        body = resp_json.get("body")
        illust = body.get("illust")

        # 如果默认用的顶部，搜索出的可能是 illust或者illustManga
        if not illust:
            illust = body.get("illustManga")

        data = illust.get("data")

        if data:
            for item in data:
                illust_id: str = str(item.get("id"))
                if illust_id not in self.history:
                    self.history.add(illust_id)
                    url = "https://www.pixiv.net/artworks/" + illust_id
                    self.random_sleep(self.random_sleep_time)
                    yield scrapy.Request(url=url, callback=self.parse_artwork)
                else:
                    print(f"Duplicate illust id: {illust_id}")

            self.now_page += 1
            if self.now_page <= self.end_page:
                next_url = self.shape_page_url(self.now_page)
                print(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}: Start search page {self.now_page}")
                yield scrapy.Request(url=next_url, callback=self.parse_page)
        else:
            print("Empty page, scrapy down")

    def parse_artwork(self, response, **kwargs):
        resp_text = response.text
        pattern = re.compile(f'"original":"(?P<url>.*?)"', re.S)
        p0_url = pattern.search(resp_text).group("url")
        print(f"Start download picture: {p0_url}")
        yield scrapy.Request(url=p0_url, callback=self.parse_picture)

    def parse_picture(self, response: scrapy.http.response.Response, **kwargs):
        if response.status == 200:
            name = response.url.split("/")[-1]
            picture = response.body
            return {"name": name, "picture": picture}
