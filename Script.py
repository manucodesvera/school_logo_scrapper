import csv
import os
import sys
import time
import pandas as pd

from mixins import essentials,start_new_web_driver
import logging.config
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

ROOT_FOLDER = "media"
is_new_image = False
class Scrap(essentials):
    
    def process_scrap(self, file_path):
        crash = False
        self.delete_previous_files()
        if os.path.exists('media'):
            self.delete_old_img_folder("media", file_path)
        if os.path.exists('address.csv'):
            self.delete_old_address(file_path, 'address.csv')
        datas = pd.read_excel(file_path)
        new_df = []
        """

        I ONLY TAKING 100 DATAS FROM THE EXCEL FOR TESTING.
        YOU CAN TAKE ALL DATAS BY CHANGING THE RANGE OF THE FORLOOP
        INTO len(datas)

        """
        print("ADDRESS FETCHING STARTED\n")
        driver = start_new_web_driver()
        for i in range(len(datas)):
           if not self.is_address_exist(str(datas.iloc[i]["Id"]).rstrip()):
               data = self.adress_fetcher(
                   datas.iloc[i]["Latitude"], datas.iloc[i]["Longitude"], driver
               )
               if data.get("fail"):
                   driver = start_new_web_driver()
                   data = self.adress_fetcher(
                       datas.iloc[i]["Latitude"], datas.iloc[i]["Longitude"], driver
                   )
                   if data.get("address"):
                       new_df.append(
                           {datas.iloc[i]["FullName"] + ":ID:" + datas.iloc[i]["Id"]: data["address"]}
                       )
                   elif data.get("fail"):
                       driver = start_new_web_driver()
                       data = self.adress_fetcher(
                           datas.iloc[i]["Latitude"], datas.iloc[i]["Longitude"], driver
                       )
                       if data.get("address"):
                           new_df.append(
                               {datas.iloc[i]["FullName"] + ":ID:" + datas.iloc[i]["Id"]: data["address"]}
                           )
                       elif data.get("fail"):
                           crash = True
                           logger.debug(
                               f'ERROR:Driver Failure, FUNCTION:adress_fetcher, MESSAGE: Driver Crashed on fetching {i} address')
                           break

               elif data.get("address"):
                   new_df.append(
                       {datas.iloc[i]["FullName"] + ":ID:" + datas.iloc[i]["Id"]: data["address"]}
                   )
        if new_df:
            self.write_all_address_csv(new_df)
        if crash == True:
            driver = start_new_web_driver()
        print("ADDRESS FETCHING COMPLETED\n")
        if os.path.exists("webaddress.csv"):
            self.delete_old_web_address("address.csv", "webaddress.csv")
        print("WEB ADDRESS FETCHING STARTED\n")
        web_address = self.scrap_website("address.csv", driver)
        driver.quit()
        web_address_csv = self.write_all_webaddress_csv(web_address)
        print("WEB ADDRESS FETCHING COMPLETED\n")
        web_address = pd.read_csv(web_address_csv)
        with open("issue.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["School Name", "Web Address", "Issue"])
            logo_df = []
            print("LOGOS LINK FETCHING STARTED\n")
            for i in range(len(web_address)):
                id = str(web_address.iloc[i]["School Name"].split(":ID:")[1])
                if not self.is_image_or_directory_exist(id):
                    result = self.fetch_logo_links(
                        str(web_address.iloc[i]["School Name"].split(":ID:")[0]).replace(
                            "/", ""
                        ),
                        web_address.iloc[i]["Web Address"],
                        str(web_address.iloc[i]["School Name"].split(":ID:")[1]),
                    )
                    if result:
                        if type(result) is list:
                            for datas in result:
                                logo_df.append(datas)
                        elif (
                            result.get(web_address.iloc[i]["School Name"])
                            == "LOGO NOT FOUND"
                        ):
                            writer.writerow(
                                [
                                    f"{str(web_address.iloc[i]['School Name'])}",
                                    f"{web_address.iloc[i]['Web Address']}",
                                    "LOGO NOT FOUND",
                                ]
                            )
                        else:
                            writer.writerow(
                                [
                                    f"{str(web_address.iloc[i]['School Name'])}",
                                    f"{web_address.iloc[i]['Web Address']}",
                                    "ERROR OCCURRED WHILE TRYING TO REQUEST THE WEBPAGE",
                                ]
                            )
                    else:
                        writer.writerow(
                            [
                                f"{str(web_address.iloc[i]['School Name'])}",
                                f"{web_address.iloc[i]['Web Address']}",
                                "NONE OF THE CONDITIONS SATISFIED",
                            ]
                        )
                    time.sleep(1)
            grouped_data = {}
            for logo_dict in logo_df:
                school_name, logo_url = list(logo_dict.items())[0]

                if school_name in grouped_data:
                    grouped_data[school_name].append(logo_url)
                else:
                    grouped_data[school_name] = [logo_url]
            print("LOGOS LINK FETCHING COMPLETED\n")

            print("LOGO DOWNLOADING STARTED\n")
            for key, value in grouped_data.items():
                if len(grouped_data[key]) > 1:
                    count = 0
                    for data in grouped_data[key]:
                        count += 1
                        error = self.download_image(ROOT_FOLDER, data, str(key), count)
                        if error:
                            writer.writerow(
                                [
                                    list(error.keys())[0],
                                    error[list(error.keys())[0]],
                                    "FAILED TO DOWNLOAD IMAGE",
                                ]
                            )
                else:
                    data = grouped_data[key][0]
                    error = self.download_image(ROOT_FOLDER, data, str(key))
                    if error:
                        writer.writerow(
                            [
                                list(error.keys())[0],
                                error[list(error.keys())[0]],
                                "FAILED TO DOWNLOAD IMAGE",
                            ]
                        )
            print("LOGO DOWNLOADING COMPLETED")

b1 = Scrap()
file_path = sys.argv[1]
b1.process_scrap(file_path)
