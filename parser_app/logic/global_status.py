import pandas as pd
from datetime import datetime, timedelta, date
import parser_app
from anehome.settings import BASE_DIR
import os
from selenium import webdriver


class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class Global(Singleton):

    succ_proxies = []

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))  # handlers/
        self.links = pd.read_csv(os.path.join(self.base_dir, r'description/final_links.csv'), sep=';', index_col=0)
        self.gks_links = os.path.join(self.base_dir, r'description/gks_weekly_links.csv')
        self.path_desc = os.path.join(self.base_dir, r'description/categories.csv')
        self.example_shot = os.path.join(self.base_dir, r'description/data_2019-10-02.csv')
        self.desc_df = pd.read_csv(self.path_desc, sep=';', index_col='id')
        self.date = date(year=2021, month=9, day=13)  # datetime.now().date() #
        self.max_links = None
        self.is_selenium_ozon = False
        self.is_selenium_okey = False
        self.is_selenium_utkonos = False
        self.is_shutdown = False
        self.path_chromedriver = os.path.join(BASE_DIR, 'chromedriver')  # '/home/yelex/PycharmProjects/ane_django/chromedriver'
        self.path_parsedcontent = os.path.join(BASE_DIR, 'parsed_content')
        options = webdriver.ChromeOptions()

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.chrome_options = options
        self.path_sfb = os.path.join(self.base_dir, r'description/sfb.csv')

    def getproxies(self):
        parser_app.logic.handlers.tools.get_proxy('https://www.vprok.ru/', get_new=True, get_list=True)
        # print('self.proxies:', self.proxies)

    def setstatus(self, status):
        self.status = status









