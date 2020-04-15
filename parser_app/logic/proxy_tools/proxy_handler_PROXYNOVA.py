import time
from typing import List

from bs4 import BeautifulSoup

from parser_app.logic.global_status import get_usual_webdriver
from parser_app.logic.handlers.tools import remove_odd_space


class ProxynovaProxyHandler:

    def get_name(self) -> str:
        return "proxynova.com"

    def get_proxy_list(self, port: int = 3128) -> List[str]:

        driver = get_usual_webdriver()
        driver.get('https://www.proxynova.com/proxy-server-list/')
        time.sleep(7.5)
        ips = []
        try:
            page = driver.page_source
            soup = BeautifulSoup(page, 'html.parser')
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
