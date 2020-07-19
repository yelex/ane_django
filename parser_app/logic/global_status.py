import sys

import pandas as pd
from datetime import datetime

from selenium.common.exceptions import WebDriverException
from tbselenium.exceptions import TBDriverPortError
from tbselenium.tbdriver import TorBrowserDriver

from parser_app.logic.handlers.tools import get_proxy
from anehome.settings import BASE_DIR, DEVELOP_MODE
import os
from selenium import webdriver

from anehome.utils import static_variables


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
        self.links = pd.read_csv(os.path.join(self.base_dir, os.path.join('description', 'final_links.csv')), sep=';',
                                 index_col=0)
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

        self.path_chromedriver = os.path.join(BASE_DIR,
                                              'chromedriver')  # '/home/yelex/PycharmProjects/ane_django/chromedriver'
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
        elif sys.platform == 'darwin':
            self.path_chromedriver = os.path.join('ChromeDriver', 'chromedriver_mac')
        elif 'win' in sys.platform:
            self.path_chromedriver = os.path.join('ChromeDriver', 'chromedriver.exe')
        else:
            raise ValueError("find chrome driver for your OS on site:\n"
                             "https://chromedriver.chromium.org/downloads")

    def getproxies(self):
        if not hasattr(self, 'already_make_proxy'):
            self.already_make_proxy = True
            get_proxy('https://www.perekrestok.ru/', get_new=True, get_list=True)

    def setstatus(self, status):
        self.status = status


def get_path_to_webdriver() -> str:
    # chose chrome driver appropriate for current operation system
    if sys.platform.startswith('linux'):
        path_to_chrome_driver = os.path.join('ChromeDriver', 'chromedriver_Linux')
    elif sys.platform == 'darwin':
        path_to_chrome_driver = os.path.join('ChromeDriver', 'chromedriver_mac')
    elif 'win' in sys.platform:
        path_to_chrome_driver = os.path.join('ChromeDriver', 'chromedriver.exe')
    else:
        raise ValueError(
            "find chrome driver for your OS on site:\n"
            "https://chromedriver.chromium.org/downloads"
        )

    return path_to_chrome_driver


def get_usual_webdriver() -> webdriver.Chrome:
    """
    Create simple selenium web chrome driver
    :return: webdriver.Chrome
    """
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(executable_path=get_path_to_webdriver(), options=options)
    return driver


def create_webdriver_with_proxy(proxy_ip_with_port: str) -> webdriver.Chrome:
    """
    Create simple selenium web chrome driver with proxy
    :return: webdriver.Chrome
    """
    assert isinstance(proxy_ip_with_port, str), "proxy_ip_with_port should be string like '255.255.0.1:8080'"
    return create_webdriver(proxy_ip_with_port=proxy_ip_with_port)


def create_webdriver(**kwargs) -> webdriver.Chrome:
    """
    Create selenium web driver with params from kwargs.
    :param kwargs: can contain:
        - proxy_ip_with_port - proxy
        - download_path - path for downloaded content
    :return: webdriver.Chrome
    """
    options = webdriver.ChromeOptions()

    if 'proxy_ip_with_port' in kwargs.keys():
        options.add_argument(f"--proxy-server={kwargs['proxy_ip_with_port']}")

    if 'download_path' in kwargs.keys():
        options.add_experimental_option(
            "prefs",
            {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": kwargs['download_path'],
            },
        )

    driver = webdriver.Chrome(executable_path=get_path_to_webdriver(), options=options)
    return driver


@static_variables(already_add=False)
def _add_geckodriver_to_path() -> None:
    if _add_geckodriver_to_path.already_add:
        return
    abs_path_to_project = os.path.join(os.path.abspath(os.path.curdir), 'geckodriver')
    if sys.platform.startswith('linux'):
        path_to_geckodriver = 'linux'
    elif sys.platform == 'darwin':
        path_to_geckodriver = 'mac'
    elif 'win' in sys.platform:
        path_to_geckodriver = 'windows'
    else:
        raise ValueError(
            "Unfortunately there aren't preloaded geckodriver for yor OS\\"
            'Visit:\nhttps://github.com/mozilla/geckodriver/releases and load needed version'
        )
    sys.path.append(os.path.join(abs_path_to_project, path_to_geckodriver))
    if DEVELOP_MODE:
        print('\ncurrent PATH:\n', "\n".join(sys.path), '\n***\n', sep='')


def create_tor_webdriver() -> TorBrowserDriver:
    """
    Create Selenium Tor Web driver and load test page.
    :return: TorBrowserDriver
    """
    _add_geckodriver_to_path()

    try:
        cur_path = os.path.abspath(os.curdir)
        driver = TorBrowserDriver('tor_browser_folder')
        driver.load_url('https://check.torproject.org', wait_for_page_body=True)
        os.chdir(cur_path)
        return driver
    except TBDriverPortError:
        print('Probably you need to install Tor Service\non linux try this:\nsudo apt-get install tor\n')
        raise TBDriverPortError
    except WebDriverException:
        print('Probably you have uncompatible geckodriver\n'
              'then visit:\nhttps://github.com/mozilla/geckodriver/releases\n'
              'But, may be, you just have no geckodriver in you PATH then just add it there :)\n')
        raise WebDriverException
