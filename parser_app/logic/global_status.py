import sys

import pandas as pd
from datetime import datetime, timedelta, date

from selenium import webdriver

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
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.example_shot = os.path.join(self.base_dir, 'description', 'data_2019-10-02.csv')
        self.links = pd.read_csv(os.path.join(self.base_dir, os.path.join('description', 'final_links.csv')), sep=';', index_col=0)
        self.gks_links = os.path.join(self.base_dir, os.path.join('description', 'gks_weekly_links.csv'))
        self.path_desc = os.path.join(self.base_dir, os.path.join('description', 'categories.csv'))

        self.desc_df = pd.read_csv(self.path_desc, sep=';', index_col='id')
        self.date = datetime.now().date()  # date(year=2020, month=3, day=31)
        self.max_links = None
        self.is_selenium_ozon = False
        self.is_selenium_okey = False
        self.is_selenium_utkonos = False
        self.is_shutdown = False

        self.path_chromedriver = get_path_to_webdriver()
        self._make_proxy = False

        if not hasattr(self, 'already_make_proxy'):
            self.getproxies()

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

        # chose chrome driver appropriate for current operation system
        print(f'Use chrome driver for you operation system : {sys.platform}')
        if sys.platform.startswith('linux'):
            self.path_chromedriver = os.path.join('ChromeDriver', 'chromedriver_Linux')

        elif sys.platform.contain('win'):
            self.path_chromedriver = os.path.join('ChromeDriver', 'chromedriver.exe')
        else:
            raise ValueError("find chrome driver for your OS on site:\n"
                             "https://chromedriver.chromium.org/downloads")

    def getproxies(self):
        if not hasattr(self, 'already_make_proxy'):
            self.already_make_proxy = True
            parser_app.logic.handlers.tools.get_proxy('https://www.perekrestok.ru/', get_new=True, get_list=True)


    def setstatus(self, status):
        self.status = status


def get_path_to_webdriver() -> str:
    # chose chrome driver appropriate for current operation system
    if sys.platform.startswith('linux'):
        path_to_chrome_driver = os.path.join('ChromeDriver', 'chromedriver_Linux')
    elif sys.platform == ('darwin'):
        path_to_chrome_driver = os.path.join('ChromeDriver', 'chromedriver.exe')
    elif 'win' in sys.platform:
        path_to_chrome_driver = os.path.join('ChromeDriver', 'chromedriver.exe')
    else:
        raise ValueError(
            "find chrome driver for your OS on site:\n"
            "https://chromedriver.chromium.org/downloads"
        )

    return path_to_chrome_driver


def get_usual_webdriver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(executable_path=get_path_to_webdriver(), options=options)

    return driver


def create_webdriver_with_proxy(proxy_ip_with_port: str) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument(f'--proxy-server={proxy_ip_with_port}')
    driver = webdriver.Chrome(executable_path=get_path_to_webdriver(), options=options)

    return driver
