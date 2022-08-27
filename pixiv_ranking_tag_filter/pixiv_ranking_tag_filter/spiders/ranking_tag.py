import re
import time

import scrapy


class RankingTagSpider(scrapy.Spider):
    name = "ranking_tag"
    allowed_domains = ["www.pixiv.net", "i.pximg.net"]
    start_urls = ["https://www.pixiv.net/ranking.php?p=1&format=json"]
    # require_tags = ["風景", "风景"]
    require_tags = ["原神", "genshin", "genshin impact"]
    end_page = 10  # 排行榜最多10

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
        "LOG_LEVEL": "INFO"
    }

    def start_requests(self):
        print(f"Start ranking page: {self.start_urls[0]}")
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_ranking_page)

    def parse_ranking_page(self, response, **kwargs):
        resp_json = response.json()
        contents = resp_json.get("contents")
        for content in contents:
            tags = content.get("tags")
            illust_id = content.get("illust_id")
            for require_tag in self.require_tags:
                if require_tag in tags:
                    url = "https://www.pixiv.net/artworks/" + str(illust_id)
                    print(f"Certificate on tag *{require_tag}*: {url} ")
                    yield scrapy.Request(url=url, callback=self.parse_artwork)

        pattern = re.compile(r"\?p=(?P<page>\d+)&", re.S)
        now_page = int(pattern.search(response.url).group("page"))
        next_page = now_page + 1
        next_page_url = "https://www.pixiv.net/ranking.php?p=" + str(next_page) + "&format=json"
        if next_page <= self.end_page:
            print(f"Start ranking page: {next_page_url}")
            yield scrapy.Request(url=next_page_url, callback=self.parse_ranking_page)

    def parse_artwork(self, response, **kwargs):
        resp_text = response.text
        pattern = re.compile(f'"original":"(?P<url>.*?)"', re.S)
        p0_url = pattern.search(resp_text).group("url")

        # 多图优化，其实很肥时间，不如不用，基本上都是一图
        # pages = ["p" + str(i) for i in range(0, 5)]
        # for page in pages:
        #     url = p0_url.replace("p0", page)
        #     print(url)
        #     yield scrapy.Request(url=url, callback=self.parse_picture)

        yield scrapy.Request(url=p0_url, callback=self.parse_picture)

    def parse_picture(self, response: scrapy.http.response.Response, **kwargs):
        if response.status == 200:
            name = response.url.split("/")[-1]
            picture = response.body
            return {"name": name, "picture": picture}
