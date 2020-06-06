import json
import os
import time
from typing import List, Union

from bs4 import BeautifulSoup
from selenium import webdriver

from parser_app.logic.handlers.handler_interface import HandlerInterface
from parser_app.logic.handlers.handler_tools import ParsedProduct, get_empty_parsed_product_dict
from parser_app.logic.handlers.handler_tools import remove_odd_space, remove_non_digits


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
        :return: True if can use
        """
        return True

    def make_search_url(self, search_word) -> str:
        return rf"https://www.svyaznoy.ru/search?q={search_word}"

    def get_test_ulr(self) -> str:
        return r"https://www.svyaznoy.ru"

    def _get_parsed_product_from_search(self, category_row) -> Union[None, List[ParsedProduct]]:
        if category_row['sub_type'] != 'appliances':
            return None

        parsed_product_list = []

        url = self.make_search_url(category_row['search_word'])

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        print(f'using url:\n{url}')

        page_source = self._load_page_with_TL(url, 10.0)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return None

        soup = BeautifulSoup(page_source, 'html.parser')

        for parsed_item in soup.find_all('div', class_='b-product-block'):
            try:
                parsed_product = get_empty_parsed_product_dict()

                # title
                title = remove_odd_space(parsed_item.find('div', class_='b-product-block__name').text)
                try:
                    sub_title = remove_odd_space(parsed_item.find('div', class_='b-product-block__type').text)
                    title = sub_title + ' ' + title
                except:
                    pass

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
                print("can't parse svaznoy item")
                print(parsed_item)

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> Union[None, ParsedProduct]:

        page_source = self._load_page_with_TL(url, 10.0)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return None

        soup = BeautifulSoup(page_source, 'html.parser')

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

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
