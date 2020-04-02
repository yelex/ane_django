import sys

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
<<<<<<< HEAD
        self.base_dir = os.path.dirname(os.path.abspath(__file__))  # handlers/
        self.links = pd.read_csv(os.path.join(self.base_dir, r'description/final_links.csv'), sep=';', index_col=0)
        self.gks_links = os.path.join(self.base_dir, r'description/gks_weekly_links.csv')
        self.path_desc = os.path.join(self.base_dir, r'description/categories.csv')
        self.example_shot = os.path.join(self.base_dir, r'description/data_2019-10-02.csv')
=======
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.links = pd.read_csv(os.path.join(self.base_dir, os.path.join('description', 'final_links.csv')), sep=';', index_col=0)
        self.gks_links = os.path.join(self.base_dir, os.path.join('description', 'gks_weekly_links.csv'))
        self.path_desc = os.path.join(self.base_dir, os.path.join('description', 'categories.csv'))
>>>>>>> 9eefd47475e69e97ff29e40ef3c0e1dc4aaf992d
        self.desc_df = pd.read_csv(self.path_desc, sep=';', index_col='id')
        self.date = datetime.now().date()  # date(year=2020, month=3, day=31)
        self.max_links = None
        self.is_selenium_ozon = False
        self.is_selenium_okey = False
        self.is_selenium_utkonos = False
        self.is_shutdown = False
<<<<<<< HEAD
        self.path_chromedriver = os.path.join(BASE_DIR, 'chromedriver')  # '/home/yelex/PycharmProjects/ane_django/chromedriver'
        self.path_parsedcontent = os.path.join(BASE_DIR, 'parsed_content')
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument("--disable-dev-shm-usage");
        # options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.chrome_options = options
        self.path_sfb = os.path.join(self.base_dir, r'description/sfb.csv')
=======

        # chose chrome driver appropriate for current operation system
        print(f'Use chrome driver for you operation system : {sys.platform}')
        if sys.platform.startswith('linux'):
            self.path_chromedriver = os.path.join('ChromeDriver', 'chromedriver_Linux')
        elif sys.platform.contain('win'):
            self.path_chromedriver = os.path.join('ChromeDriver', 'chromedriver.exe')
        else:
            raise ValueError("find chrome driver for your OS on site:\n"
                             "https://chromedriver.chromium.org/downloads")
>>>>>>> 9eefd47475e69e97ff29e40ef3c0e1dc4aaf992d

    def getproxies(self):
        parser_app.logic.handlers.tools.get_proxy('https://www.perekrestok.ru/', get_new=True, get_list=True)
        # print('self.proxies:', self.proxies)

    def setstatus(self, status):
        self.status = status
<<<<<<< HEAD








=======
>>>>>>> 9eefd47475e69e97ff29e40ef3c0e1dc4aaf992d
