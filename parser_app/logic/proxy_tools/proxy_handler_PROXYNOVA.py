import time
from typing import List

from bs4 import BeautifulSoup

from parser_app.logic.global_status import get_usual_webdriver
from parser_app.logic.handlers.handler_tools import remove_odd_space, load_page_with_TL


class ProxynovaProxyHandler:

    def get_name(self) -> str:
        return "proxynova.com"

    def get_proxy_list(self, port: int = 3128) -> List[str]:

        driver = get_usual_webdriver()
        page_source = load_page_with_TL(driver, 'https://www.proxynova.com/proxy-server-list/', 7.5)
        if page_source is None:
            # fixme - log - error - can't load web page
            print(f"can't load page for {self.get_name()}")
            return []
        ips = []
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            driver.quit()

            for item in soup.find('tbody').find_all('tr'):
                try:
                    extracted_ip = remove_odd_space(item.find('abbr').text).split(';')[1]
                    extracted_port = remove_odd_space(item.find_all('td')[1].text)
                    ips.append(f"{extracted_ip}:{extracted_port}")
                except:
                    pass
        finally:
            driver.quit()
            return ips
