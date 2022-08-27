# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/8/27 17:13

from selenium import webdriver

options = webdriver.ChromeOptions()

# 启用无头
# options.add_argument("--headless")

# 屏蔽webdriver
options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('--proxy-server=http://127.0.0.1:7890')
driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

cookies_vip_fp = "./cookies_vip.txt"

with open(cookies_vip_fp, "r") as f:
    cookies_str = f.read()
    cookies_li = cookies_str.split(";")
    cookies_dict_li: list[dict] = []
    for content in cookies_li:
        key = content.split("=")[0].strip(" ")
        value = content.split("=")[-1].strip(" ")
        cookies_dict_li.append({"domain": ".pixiv.net", "name": key, "value": value})

url = "https://www.pixiv.net/"
driver.get(url)

for cookies_dict in cookies_dict_li:
    print(cookies_dict)
    driver.add_cookie(cookies_dict)

driver.refresh()
