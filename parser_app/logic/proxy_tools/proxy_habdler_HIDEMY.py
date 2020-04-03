import time
from typing import List

from bs4 import BeautifulSoup

from parser_app.logic.global_status import get_usual_webdriver
from parser_app.logic.proxy_tools.proxy_habdler_interface import ProxyHandlerInterface


class HidemyProxyHandler(ProxyHandlerInterface):

    def get_name(self) -> str:
        return "hidemy_proxy_handler"

    def get_proxy_list(self, port: str = 3128) -> List[str]:

        driver = get_usual_webdriver()
        driver.get(f"https://hidemy.name/ru/proxy-list/?maxtime=300&ports={port}#list")
        time.sleep(7.5)
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        driver.quit()

        ips = []
        try:
            for item in soup.find('div', class_='table_block').find('tbody').find_all('tr'):
                lst = item.find_all('td')

                # ip and port
                ips.append(f"{lst[0].text}:{lst[1].text}")
        except:
            print('smt wrong with parsing proxy page')
            print(soup.find('div', class_='table_block'))

        return ips
