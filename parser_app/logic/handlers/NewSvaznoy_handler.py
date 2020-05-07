import json
import os
import time
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver

from parser_app.logic.handlers.handler_interface import HandlerInterface
from parser_app.logic.handlers.handler_tools import ParsedProduct, get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import remove_odd_space, remove_non_digits


class SvaznoyHandlerInterface(HandlerInterface):

    # implement in every real handler
    def get_handler_name(self) -> str:
        """
        :return: string, without spaces, represent current handler
        """
        raise NotImplemented("Implement me! I'm just an interface!")

    def test_web_driver(self, driver: webdriver.Chrome) -> bool:
        """
        This function should test webdriver for suit this concrete site handler
        This can be not changed in real handlers, cause there are simple test to connections.

        :param driver: webdriver.Chrome
        :return: True if cat use
        """
        return True

    def make_search_url(self, search_word) -> str:
        return rf"https://www.svyaznoy.ru/search?q={search_word}"

    def get_test_ulr(self) -> str:
        return r"https://www.svyaznoy.ru"

    def _get_parsed_product_from_search(self, category_row) -> List[ParsedProduct]:
        if category_row['sub_type'] != 'appliances':
            return []

        parsed_product_list = []

        url = self.make_search_url(category_row['search_word'])

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        print(f'using url:\n{url}')

        self._driver.get(url)

        time.sleep(2.0)

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        for parsed_item in soup.find_all('div', class_='product'):
            try:
                parsed_product = get_empty_parsed_product_dict()

                # title
                title = remove_odd_space(parsed_item.find('div', class_='b-product-block__name').text)
                try:
                    sub_title = remove_odd_space(parsed_item.find('div', class_='b-product-block__type').text)
                except:
                    sub_title = ""
                if sub_title != "":
                    title = sub_title + ' ' + title
                parsed_product['title'] = title

                # url
                url = parsed_item.find('a', class_='b-product-block__main-link')['href']
                url = fr'https://www.svyaznoy.ru{url}'
                parsed_product['url'] = url

                # price
                price = remove_non_digits(parsed_item.find('span', class_='b-product-block__visible-price').text)
                parsed_product['price_new'] = price

                parsed_product_list.append(parsed_product)
            except:
                # FIXME log fatal
                print("can't parse rigla item")
                print(parsed_item)

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:
        self._driver.get(url)

        time.sleep(5.0)

        page = self._driver.page_source

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

        soup = BeautifulSoup(page, 'html.parser')

        # title
        title = remove_odd_space(soup.find('h1', class_='b-offer-title').text)
        parsed_product['title'] = title

        # price
        price = remove_non_digits(soup.find('div', class_='b-offer-box__price').text)
        parsed_product['price_new'] = price

        return parsed_product

    def _get_cookie(self) -> List:
        raise NotImplemented("Implement me! I'm just an interface!")


class SvaznoyHandlerMSK(SvaznoyHandlerInterface):
    def get_handler_name(self) -> str:
        return "svaznoy_msk"

    def _get_cookie(self) -> List:
        return json.load(open(
            os.path.join('parser_app', 'logic', 'handlers', 'cookie_sets', 'svaznoy_msk_chrome.json'),
            'r'
        ))
