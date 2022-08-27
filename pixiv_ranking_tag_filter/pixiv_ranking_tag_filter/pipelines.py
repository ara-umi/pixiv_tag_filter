# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os.path
import time


class PixivRankingTagFilterPipeline(object):
    file_dir = "./picture/" + time.strftime("%Y.%m.%d.%H.%M.%S", time.localtime(time.time()))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    def process_item(self, item, spider):
        name = item.get("name")
        # name = name.replace("_p0", "")  # 尾缀可能是p0可能是ugoira0，很麻烦，我也不清楚
        picture = item.get("picture")

        assert name, "Invalid name"
        assert picture, "Empty picture body"

        with open(self.file_dir + "/" + name, "wb") as f:
            f.write(picture)

        print(f"\tDown: {name}")
        return item
