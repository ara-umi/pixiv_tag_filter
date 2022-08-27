# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import os

log_dir = "./log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

picture_dir = "./picture"
if not os.path.exists(picture_dir):
    os.makedirs(picture_dir)