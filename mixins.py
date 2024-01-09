
import os
import time
import csv
import shutil
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import InvalidSessionIdException
from selenium.common.exceptions import WebDriverException
from conditions import (
    if_header_img,
    if_image_in_headers_anchor,
    if_image_tags,
    if_image_tags_in_anchor,
    if_images_with_school_name,
)

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
def start_new_web_driver():
    chromedriver_path = "chromedriver"
    os.environ["PATH"] += os.pathsep + chromedriver_path
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    # options.add_argument('--headless')
    options.add_argument("--incognito")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver

class essentials:
    def delete_previous_files(self):
        if os.path.exists("issue.csv"):
            os.remove("issue.csv")

    def adress_fetcher(self, latitude, longitude, driver, retry=False):
        print(f"====> Fetching Address of school using latitude:{latitude} and longitude:{longitude}")
        try:
            driver.get(f"https://www.google.com/maps?q={latitude},{longitude}")
            driver.implicitly_wait(10)
            address = None
            try:
                if driver.find_element(By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]'):
                    element = driver.find_element(By.XPATH,
                                              '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div')

                    actions = ActionChains(driver)
                    actions.move_to_element(element).perform()

                    element.click()
                    driver.implicitly_wait(10)
            except Exception as e:
                logger.debug(f'ERROR:No Cookie page, FUNCTION:adress_fetcher')

            driver.implicitly_wait(10)
            try:
                address = driver.find_element(By.XPATH, "//div[@data-tooltip='Adresse kopieren']//span[@class='DkEaL']")
                driver.execute_script("arguments[0].scrollIntoView();", address)
                time.sleep(2)
                if address.text == "":
                    address = driver.find_element(By.XPATH, "//div[@data-tooltip='Adresse kopieren']//span[@class='DkEaL']")
                    driver.execute_script("arguments[0].scrollIntoView();", address)
                    address = address.text
                else:
                    address = address.text
            except NoSuchElementException as e:
                logger.debug(f'ERROR:No address to copy, FUNCTION:adress_fetcher')
            return {"address": address}
        except InvalidSessionIdException:
            driver.quit()
            time.sleep(1)
            return {"fail": "fail"}

        except WebDriverException:
            driver.quit()
            time.sleep(1)
            return {"fail": "fail"}


    def write_all_address_csv(self, datas):
        file_path = "address.csv"
        if os.path.exists(file_path):
            records = []
            for school_data in datas:
                school_name, address = list(school_data.items())[0]
                records.append([school_name, address])
            df = pd.DataFrame(records)
            df.to_csv(f"{file_path}", mode="a", index=False, header=False)
            return file_path
        else:
            records = []
            for school_data in datas:
                school_name, address = list(school_data.items())[0]
                records.append([school_name, address])
            df = pd.DataFrame(records, columns=["School Name", "Address"])
            df.to_csv(f"{file_path}", mode="w", index=False)
            return file_path

    def scrap_website(self, address, driver):
        wait = WebDriverWait(driver, 20)
        datas = pd.read_csv(address)
        wed_data = []
        for i in range(len(datas)):
            if not self.is_web_address_exist(datas.iloc[i]["School Name"].split(":ID:")[1]):
                name = datas.iloc[i]["School Name"].split(":ID:")[0]
                name = name.replace(".", "").replace("/", " ")
                print(f"====> Fetching Web Address of School : {name}")
                search_text = datas.iloc[i]["Address"]
                if name not in search_text:
                    search_text = str(name) + " " + str(search_text)
                time.sleep(1)
                try:
                    driver.get(f"https://in.search.yahoo.com/")
                    driver.implicitly_wait(10)
                    try:
                        go_to_end = driver.find_element(By.XPATH, '//*[@id="scroll-down-btn"]')
                        go_to_end.click()
                        time.sleep(1)
                        accept_cookie = driver.find_element(By.XPATH, '//*[@id="consent-page"]/div/div/div/form/div[2]/div[2]/button[1]')
                        accept_cookie.click()
                    except:
                         logger.debug(f'ERROR:No coookie page in yahoo, FUNCTION:adress_fetcher')
                    driver.implicitly_wait(5)
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
                            href_value = self.alternate_way(search_text,driver, wait)
                            if href_value:
                                if "gov" not in str(href_value):
                                    wed_data.append(
                                        {datas.iloc[i]["School Name"]: href_value}
                                    )
                except Exception as e:
                    logger.debug(
                        f'ERROR: {type(e)}, FUNCTION:scrap_website, KEYWORD:{search_text}')
        driver.quit()
        return wed_data

    def alternate_way(self, search_text, driver, wait):
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
        if os.path.exists(file_path):
            records = []
            for web_data in datas:
                school_name, address = list(web_data.items())[0]
                records.append([school_name, address])
            df = pd.DataFrame(records)
            df.to_csv(f"webaddress.csv", mode="a", index=False, header=False)
            return file_path
        else:
            records = []
            for web_data in datas:
                school_name, address = list(web_data.items())[0]
                records.append([school_name, address])
            df = pd.DataFrame(records, columns=["School Name", "Web Address"])
            df.to_csv(f"{file_path}", mode="w", index=False)
            return file_path

    def fetch_logo_links(self, school_name, web_address, school_id):
        print(f"====> Fetching Logo link of School : {school_name}")
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
            new_folder_path = os.path.join(rootfolder, f'{groupfolder.split(":ID:")[0].replace(":", "")}__{groupfolder.split(":ID:")[1]}')
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
                    print(f"===>Downloading Image in path : {img_path}")
                else:
                    img_path = f"{rootfolder}/{groupfolder.split(':ID:')[1]}.jpeg"
                    img_path = img_path.replace("//", "/")
                    img_path = img_path.replace(":", "")
                    with open(img_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=128):
                            file.write(chunk)
                    print(f"===>Downloading Image in path : {img_path}")
            else:
                logger.debug(
                    f'ERROR:{response.status_code}, FUNCTION:download_image, SCHOOL:{groupfolder}, LOGO-LINK:{img_data}')
                return {groupfolder: img_data}
        except Exception as e:
            logger.debug(f'ERROR:{type(e)}, FUNCTION:download_image, SCHOOL:{groupfolder}, LOGO-LINK:{img_data}')

    def is_address_exist(self,id):
        if os.path.exists("address.csv"):
            with open('address.csv', 'rt') as f:
                reader = csv.reader(f, delimiter=',')
                for index, row in enumerate(reader):
                    if index >= 1:
                        if str(id).strip() in str(row[0]).split(":ID:")[1]:
                            return True
                return False
        else:
            return False

    def is_web_address_exist(self,id):
        if os.path.exists("webaddress.csv"):
            with open('webaddress.csv', 'rt') as f:
                reader = csv.reader(f, delimiter=',')
                for index, row in enumerate(reader):
                    if index >= 1:
                        if str(id).strip() in str(row[0]).split(":ID:")[1]:
                            return True
                return False
        else:
            return False


    def delete_old_address(self,excel_file_path, csv_file_path):

        df_csv = pd.read_csv(csv_file_path)

        df_excel = pd.read_excel(excel_file_path)

        column_to_check = 'School Name'

        rows_to_keep = []
        for index, row in df_csv.iterrows():
            if row[column_to_check].split(':ID:')[1] in df_excel['Id'].values:
                rows_to_keep.append(index)

        df_result = df_csv.loc[rows_to_keep]

        df_result.to_csv(csv_file_path, index=False)

    def delete_old_web_address(self,address_file_path, webaddress_file_path):

        df_address = pd.read_csv(address_file_path)

        df_web_address = pd.read_csv(webaddress_file_path)

        csv1 = df_web_address[df_web_address['School Name'].isin(df_address['School Name'])]

        csv1.to_csv(f'{webaddress_file_path}', index=False)

    def is_image_or_directory_exist(self, id_to_check):
        media_folder_path = 'media'
        if os.path.exists(media_folder_path):
            file_path = f"{media_folder_path}/{id_to_check}.jpeg"
            if os.path.exists(file_path):
                return True

            for directory_name in os.listdir(media_folder_path):
                dir_path = f"{media_folder_path}/{directory_name}"

                if os.path.exists(dir_path) and os.path.isdir(dir_path) and directory_name.endswith(id_to_check):
                    return True

    def read_excel_file(self,file_path):
        df = pd.read_excel(file_path)
        return set(df['Id'])

    def delete_old_img_folder(self,media_folder, excel_file):
        excel_ids = self.read_excel_file(excel_file)

        for root, dirs, files in os.walk(media_folder):
            for file in files:
                file_id = os.path.splitext(file)[0]
                if file_id not in excel_ids:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

            for dir in dirs:
                dir_id = str(dir).split("__")[-1]
                if dir_id not in excel_ids:
                    dir_path = os.path.join(root, dir)
                    shutil.rmtree(dir_path)