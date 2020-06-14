"""
Uncompleted part, idea in abstraction for interaction with web-pages.
"""
import time
from typing import Union, Optional, List, Dict

from selenium import webdriver

from parser_app.logic.global_status import get_path_to_webdriver


class WebDriverInterface:
    def reinit_for_baseURL(self, url: str, cookie: List[Dict] = [], max_time_out: Optional[int] = 5) -> None:
        raise NotImplemented

    def get_page_by_url(self, url: str) -> Union[str, None]:
        """
        Return page source - string, or None if error occur

        :param url:
        :return:
        """
        raise NotImplemented

    def close(self) -> None:
        raise NotImplemented


class SeleniumURLGetter(WebDriverInterface):

    def __init__(self):
        self.driver = None
        self.max_time_out: int = 5

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

    def reinit_for_baseURL(self, url: str, cookie: List[Dict] = [], max_time_out: Optional[int] = 5) -> None:
        self.close()
        options = webdriver.ChromeOptions()
        #     options.add_argument(f'--proxy-server={proxy_ip_with_port}')
        driver = webdriver.Chrome(executable_path=get_path_to_webdriver(), options=options)
        driver.set_page_load_timeout(self.max_time_out)

    def get_page_by_url(self, url: str) -> Union[str, None]:
        try:
            self.driver.get(url)
            time.sleep(self.max_time_out)
            page_source = self.driver.page_source
        except:
            self.driver.execute_script("window.stop();")
            page_source = self.driver.page_source

        return page_source
