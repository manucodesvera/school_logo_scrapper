import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from conditions import (
    if_header_img,
    if_image_in_headers_anchor,
    if_image_tags,
    if_image_tags_in_anchor,
    if_images_with_school_name,
)

import logging
import logging.config
import os

LOGGING = {
    'version': 1,
    'loggers': {
        'error_payload': {
            'handlers': ['error_log_handler'],
            'level': 'DEBUG',
        }
    },
    'handlers': {
        'error_log_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': "error.log",
            'when': 'D',
            'interval': 30,
            'backupCount': 5,
            'formatter': 'error_payload',  # Corrected formatter name here
        }
    },
    "formatters": {
        "error_payload": {
            "format": (
                u"%(asctime)s [%(levelname)-8s] "
                "%(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}

logging.config.dictConfig(LOGGING)

logger = logging.getLogger('error_payload')

chromedriver_path = "chromedriver"
os.environ["PATH"] += os.pathsep + chromedriver_path
options = webdriver.ChromeOptions()
options.add_argument('--disable-gpu')
options.add_argument('--headless')
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)


class essentials:
    def delete_previous_files(self):
        if os.path.exists("address.csv"):
            os.remove("address.csv")
        if os.path.exists("issue.csv"):
            os.remove("issue.csv")
        if os.path.exists("webaddress.csv"):
            os.remove("webaddress.csv")

    def adress_fetcher(self, latitude, longitude):
        driver.get(f"https://www.google.com/maps?q={latitude},{longitude}")
        time.sleep(2)
        address = None
        try:
            address = driver.find_element(By.XPATH, "//div[@data-tooltip='Copy address']/div[2]/span[2]/span")
            driver.execute_script("arguments[0].scrollIntoView();", address)
            time.sleep(2)
            if address.text == "":
                address = driver.find_element(By.XPATH, "//div[@data-tooltip='Copy address']//span[@class='DkEaL']")
                driver.execute_script("arguments[0].scrollIntoView();", address)
                address = address.text
            else:
                address = address.text
        except NoSuchElementException:
            logger.debug(f'ERROR:No address to coppy, FUNCTION:adress_fetcher')
        return address

    def write_all_address_csv(self, datas):
        file_path = "address.csv"
        records = []
        for school_data in datas:
            school_name, address = list(school_data.items())[0]
            records.append([school_name, address])
        df = pd.DataFrame(records, columns=["School Name", "Address"])
        df.to_csv(f"{file_path}", index=False)
        return file_path

    def scrap_website(self, address):
        datas = pd.read_csv(address)
        wed_data = []
        for i in range(len(datas)):
            name = datas.iloc[i]["School Name"].split(":ID:")[0]
            name = name.replace(".", "").replace("/", " ")
            search_text = datas.iloc[i]["Address"]
            if name not in search_text:
                search_text = str(name) + " " + str(search_text)
            time.sleep(1)
            try:
                driver.get(f"https://in.search.yahoo.com/")
                driver.implicitly_wait(10)
                input_box = wait.until(
                    EC.presence_of_element_located((By.ID, "yschsp"))
                )
                input_box.send_keys(search_text)
                input_box.send_keys(Keys.RETURN)
                driver.implicitly_wait(10)
                time.sleep(2)
                element_xpath = '//*[@id="web"]/ol'
                ol = None
                try:
                    ol = wait.until(
                        EC.presence_of_element_located((By.XPATH, element_xpath))
                    )
                except TimeoutException:
                    logger.debug(f'ERROR: TimeoutException Occurred, FUNCTION:scrap_website, KEYWORD:{search_text}')
                if ol:
                    li_tag = ol.find_element(By.TAG_NAME, "li")
                    href_value = None
                    try:
                        href_value = li_tag.find_element(
                            By.XPATH, "//li/div/div[1]/h3/a"
                        )
                    except NoSuchElementException:
                        logger.debug(
                            f'ERROR: NoSuchElementException Occurred, FUNCTION:scrap_website, KEYWORD:{search_text}')
                    if href_value and "gov" not in str(
                            href_value.get_attribute("href")
                    ):
                        wed_data.append(
                            {
                                datas.iloc[i]["School Name"]: href_value.get_attribute(
                                    "href"
                                )
                            }
                        )
                    else:
                        href_value = self.alternate_way(search_text)
                        if href_value:
                            if "gov" not in str(href_value):
                                wed_data.append(
                                    {datas.iloc[i]["School Name"]: href_value}
                                )
            except Exception as e:
                logger.debug(
                    f'ERROR: {type(e)}, FUNCTION:scrap_website, KEYWORD:{search_text}')

        return wed_data

    def alternate_way(self, search_text):
        try:
            driver.get(f"https://www.startpage.com/sp/search")
            input_box = driver.find_element(By.ID, "q")
            input_box.send_keys(search_text)
            input_box.send_keys(Keys.RETURN)
            time.sleep(1)
            driver.maximize_window()
            did_u_mean = None
            try:
                did_u_mean = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="main"]/div/section[1]/section/span')
                    )
                )
            except TimeoutException:
                logger.debug(
                    f'ERROR: TimeoutException Occurred STARTPAGE, FUNCTION:alternate_way, KEYWORD:{search_text}')
            if did_u_mean and str(did_u_mean.text) == "Did you mean:":
                xpath = '//*[@id="main"]/div/section[3]/div[1]'
            else:
                xpath = '//*[@id="main"]/div/section[2]/div[1]'
            div = wait.until(EC.presence_of_element_located((By.XPATH, f"{xpath}")))
            if div:
                href_value = div.find_element(By.XPATH, "./div[1]/div[2]/a")
                href_value = href_value.get_attribute("href")
                return href_value
        except Exception as e:
            logger.debug(
                f'ERROR: {type(e)} occured using startpage, FUNCTION:alternate_way, KEYWORD:{search_text}')

    def write_all_webaddress_csv(self, datas):
        file_path = "webaddress.csv"
        records = []
        for web_data in datas:
            school_name, address = list(web_data.items())[0]
            records.append([school_name, address])
        df = pd.DataFrame(records, columns=["School Name", "Web Address"])
        df.to_csv(f"{file_path}", index=False)
        return file_path

    def fetch_logo_links(self, school_name, web_address, school_id):
        key = str(school_name) + ":ID:" + str(school_id)
        try:
            response = requests.get(web_address)
            if response.status_code == 200:
                ALT_TEXT = str(school_name).replace("/", "")
                soup = BeautifulSoup(response.text, "html.parser")
                header_img = ""
                header = soup.find("header")
                if header:
                    header_img = header.find("img")
                img_tags = soup.find_all("img", alt=f"{ALT_TEXT}")
                images_with_alt = soup.find_all("img", alt=True)
                images_with_school_name = [
                    img
                    for img in images_with_alt
                    if f"{ALT_TEXT.lower()}" in img["alt"].lower()
                    or (
                        "," in ALT_TEXT
                        and f'{ALT_TEXT.split(",")[0].lower()}' in img["alt"].lower()
                    )
                ]
                images_with_school_name = [
                    img_tag for img_tag in images_with_school_name if img_tag.get("src")
                ]
                header_anchor_with_image = soup.select("header a img")
                matching_anchors = [
                    anchor
                    for anchor in soup.find_all(
                        "a",
                        href=lambda href: (
                            href.rstrip("/")
                            if href is not None and href != "/"
                            else href
                        )
                        in [
                            web_address.rstrip("/"),
                            "/",
                            web_address.replace("http:", "https:").rstrip("/"),
                        ],
                    )
                    if anchor.find("img")
                ]
                image_tags_in_anchor = []
                if matching_anchors:
                    for img_tag in matching_anchors:
                        image_tags_in_anchor.append(img_tag.find("img"))
                if img_tags:
                    data = if_image_tags(img_tags, web_address, key)
                    return data
                elif images_with_school_name:
                    data = if_images_with_school_name(
                        images_with_school_name, web_address, key
                    )
                    return data
                elif image_tags_in_anchor:
                    data = if_image_tags_in_anchor(
                        image_tags_in_anchor, web_address, key
                    )
                    return data
                elif header_anchor_with_image:
                    data = if_image_in_headers_anchor(
                        header_anchor_with_image, web_address, key
                    )
                    return data
                elif header_img:
                    data = if_header_img(header_img, web_address, key)
                    return data
                else:
                    return {key: "LOGO NOT FOUND"}
            else:
                logger.debug(f'ERROR:{response.status_code}, FUNCTION:fetch_logo_links, SCHOOL:{key}, WEBADDRESS:{web_address}')
                return {key: f"{web_address}"}

        except Exception as e:
            logger.debug(f'ERROR:{type(e)}, FUNCTION:fetch_logo_links, SCHOOL:{key}, WEBADDRESS:{web_address}')

    def download_image(self, rootfolder, img_data, groupfolder=None, count=None):
        new_folder_path = None
        if not os.path.exists(rootfolder):
            os.makedirs(rootfolder)

        if count:
            new_folder_path = os.path.join(rootfolder, groupfolder.split(":ID:")[0].replace(":", ""))
            os.makedirs(new_folder_path, exist_ok=True)

        if "https://" not in str(img_data) and "http://" not in str(img_data):
            img_data = str(img_data).replace("//", "http://")
        try:
            response = requests.get(img_data, stream=True)

            if response.status_code == 200:
                if new_folder_path:
                    new_folder_path = new_folder_path.replace("//", "/")
                    new_folder_path = new_folder_path.replace(":", "")

                    img_path = f"{new_folder_path}/image{count}.jpeg"
                    img_path = img_path.replace("//", "/")
                    img_path = img_path.replace(":", "")
                    with open(img_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=128):
                            file.write(chunk)
                else:
                    img_path = f"{rootfolder}/{groupfolder.split(':ID:')[1]}.jpeg"
                    img_path = img_path.replace("//", "/")
                    img_path = img_path.replace(":", "")
                    with open(img_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=128):
                            file.write(chunk)
            else:
                logger.debug(
                    f'ERROR:{response.status_code}, FUNCTION:download_image, SCHOOL:{groupfolder}, LOGO-LINK:{img_data}')
                return {groupfolder: img_data}
        except Exception as e:
            logger.debug(f'ERROR:{type(e)}, FUNCTION:download_image, SCHOOL:{groupfolder}, LOGO-LINK:{img_data}')

