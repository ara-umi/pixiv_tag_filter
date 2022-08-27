# pixiv_tag_filter
## requirement

```
# env
Python 3.9.12
scrapy 2.6.2
selenium 3.141.0 

# create env by anaconda
conda env create -n xx -f environment.yaml
```

## start spider

```python
cd {your_repository_path}\pixiv_tag_filter\pixiv_ranking_tag_filter
scrapy crawl popular/ranking_tag...
```

## spider mode

- popular: 

  After you set the tag and search conditions, pass the URL of the first page into cmd, it will automatically download all the pictures that meet the conditions, and record the picture id. Duplicate pictures will not be crawled.

  This mode needs cookies with pixiv vip.

- ranking_tag:

  Crawl all the pictures that satisfy the tag on the ranking of the day, you can change the tag in RankingTagSpider.require_tags, type list.

- tag_like:

  Search all pictures of a specific tag, filter and download the pictures. You can set the upper and lower limits of *bookmark* or *like* or*view*, alse you can set start and end page.

  This mode needs cookies 'cause visitor can only search first ten pages each tag.

## proxy

```python
change your proxy in middewares.PixivProxyMiddleware

eg.
class PixivProxyMiddleware(object):
    proxy = "http://127.0.0.1:7890"

    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxy
        return

if your don't need using proxy, simply return *process_request* 
or disable the middleware in the spider

eg.
custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # "pixiv_ranking_tag_filter.middlewares.PixivProxyMiddleware": 200,
            "pixiv_ranking_tag_filter.middlewares.PixivUserAgentMiddleware": 300,
            "pixiv_ranking_tag_filter.middlewares.PixivRefererMiddleware": 350,
        }
    }
```

## attention

- All the pictures will be dump in "./picture/" under the dir named {mode_datetime}
- History in "./history/" under the dir named {mode_datetime}
- random_sleep_time is set, request too frequently maybe cause your ip banned by pixiv for serveral minutes

 

