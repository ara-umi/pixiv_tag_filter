import scrapy


class TagLikeSpider(scrapy.Spider):
    name = "tag_like"
    allowed_domains = ["aaa"]
    start_urls = ["http://aaa/"]

    def parse(self, response, **kwargs):
        pass
