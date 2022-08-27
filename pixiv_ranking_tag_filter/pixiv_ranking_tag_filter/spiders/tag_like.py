import time
import re
from urllib.parse import quote
import random
import scrapy


class TagLikeSpider(scrapy.Spider):
    name = "tag_like"
    allowed_domains = ["www.pixiv.net", "i.pximg.net"]
    start_urls = [
        "https://www.pixiv.net/ajax/search/illustrations/here_is_content?word=here_is_contentE&order=date_d&"
        "mode=all&p=here_is_page&s_mode=s_tag_full&type=illust_and_ugoira&lang=zh"
    ]
    cookies_fp = "./cookies.txt"
    search_tag = "风景"
    start_page = 1
    end_page = 50

    now_page = start_page

    bookmark_lower_limit = 1000
    bookmark_upper_limit = None
    like_lower_limit = None
    like_upper_limit = None
    view_lower_limit = None
    view_upper_limit = None

    record_start_date = True
    start_date = None
    record_end_date = False
    end_data = None

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

    def shape_url(self, page: int) -> str:
        return self.start_urls[0].replace("here_is_content", quote(self.search_tag))\
            .replace("here_is_page", str(page))

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
        start_url = self.shape_url(self.start_page)
        # print(f"Start search page {self.now_page}: {start_url}")
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}:Start search page {self.now_page}")
        cookies = self.load_cookies()
        yield scrapy.Request(url=start_url, cookies=cookies, callback=self.parse_search_page)

    def parse_search_page(self, response, **kwargs):
        resp_json = response.json()
        error = resp_json.get("error")
        assert error != "false", f"Error occurred during spider on {response.url}"
        body = resp_json.get("body")
        illust = body.get("illust")
        data = illust.get("data")
        for item in data:
            illust_id: str = str(item.get("id"))
            tags: list = item.get("tags")

            updateDate = item.get("updateDate")
            if self.record_start_date:
                self.start_date = updateDate
                self.record_start_date = False

            url = "https://www.pixiv.net/artworks/" + illust_id
            self.random_sleep(self.random_sleep_time)
            yield scrapy.Request(url=url, callback=self.parse_artwork)

        self.now_page += 1
        if self.now_page <= self.end_page:
            next_url = self.shape_url(self.now_page)
            # print(f"Start search page {self.now_page}: {next_url}")
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}:Start search page {self.now_page}")
            yield scrapy.Request(url=next_url, callback=self.parse_search_page)


    def certificate(self, bookmark: int, like: int, view: int):
        if self.bookmark_lower_limit and not bookmark > self.bookmark_lower_limit:
            return False
        if self.like_lower_limit and not like > self.like_lower_limit:
            return False
        if self.view_lower_limit and not view > self.view_lower_limit:
            return False
        if self.bookmark_upper_limit and not bookmark < self.bookmark_upper_limit:
            return False
        if self.like_upper_limit and not like < self.like_upper_limit:
            return False
        if self.view_lower_limit and not like < self.view_upper_limit:
            return False
        return True

    def parse_artwork(self, response, **kwargs):
        resp_text = response.text
        pattern = re.compile(r'"bookmarkCount":(?P<bookmark>\d+),"likeCount":(?P<like>\d+),.*?,"viewCount":(?P<view>\d+),"', re.S)
        for res in pattern.finditer(response.body.decode("utf8")):
            bookmark = int(res.group("bookmark"))
            like = int(res.group("like"))
            view = int(res.group("view"))
            if self.certificate(bookmark, like, view):
                print(f"Certificate: {response.url}\nlike:{like} bookmark:{bookmark} view:{view}")
                # try:
                #     yield scrapy.Request(src, callback=self.parse_image, meta={"item": deepcopy(item)})
                # except TimeoutError:
                #     print(f"请求超时：", item["src"])

                pattern = re.compile(f'"original":"(?P<url>.*?)"', re.S)
                p0_url = pattern.search(resp_text).group("url")
                print(p0_url)
