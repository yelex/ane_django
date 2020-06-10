from typing import List, Union
from bs4 import BeautifulSoup
import time
import json
import os

from selenium import webdriver

from parser_app.logic.handlers.handler_interface import HandlerInterface, ParsedProduct
from parser_app.logic.handlers.handler_tools import get_empty_parsed_product_dict
from parser_app.logic.handlers.handler_tools import remove_odd_space, remove_ALL_spaces


class IkeaHandlerInterface(HandlerInterface):

    def __init__(self):
        super().__init__()

    def get_handler_name(self) -> str:
        raise NotImplemented

    def get_test_url(self) -> str:
        return r"https://www.ikea.com/ru/ru/"

    def test_web_driver(self, driver: webdriver.Chrome) -> bool:
        return True

    def _create_search_url_for_category(self, name: str) -> str:
        return rf"https://www.ikea.com/ru/ru/search/products/?q={name}"

    def _get_cookie(self) -> List:
        raise NotImplemented

    def _get_parsed_product_from_search(self, category_row) -> Union[None, List[ParsedProduct]]:
        if category_row['sub_type'] != 'furniture':
            return None

        parsed_product_list = []

        url = self._create_search_url_for_category(category_row['search_word'])

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        print(f'using url:\n{url}')

        page_source = self._load_page_with_TL(url)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return None

        soup = BeautifulSoup(page_source, 'html.parser')

        for parsed_item in soup.find_all('div', class_='product-compact__spacer'):
            try:
                parsed_product = get_empty_parsed_product_dict()

                # title
                title = remove_odd_space(parsed_item.find('span', 'product-compact__name').text)
                sub_title = remove_odd_space(parsed_item.find('span', 'product-compact__type').text)
                title += ' ' + sub_title
                parsed_product['title'] = title

                # url
                url = parsed_item.find('a')['href']
                parsed_product['url'] = url

                # price
                price = remove_ALL_spaces(
                    parsed_item.find('span', class_='product-compact__price__value').text
                )[:-1]
                parsed_product['price_new'] = price

                parsed_product_list.append(parsed_product)
            except:
                # FIXME log fatal
                print("can't parse IKEA item")
                print(parsed_item)

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> Union[None, ParsedProduct]:

        page_source = self._load_page_with_TL(url)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return None

        soup = BeautifulSoup(page_source, 'html.parser')

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

        # title
        title_item = soup.find('div', class_='product-pip__product-heading-container')
        title = remove_odd_space(title_item.find('span', class_='product-pip__name').text)
        sub_title = remove_odd_space(title_item.find('span', 'range__text-rtl').text)
        title += ' ' + sub_title
        parsed_product['title'] = title

        # price
        price = remove_ALL_spaces(soup.find('span', class_='product-pip__price__value').text)[:-1]
        parsed_product['price_new'] = price

        return parsed_product


class IkeaHandlerSPB(IkeaHandlerInterface):
    def get_handler_name(self) -> str:
        return "ikea_spb"

    def _get_cookie(self) -> List:
        return json.load(open(
            os.path.join('parser_app', 'logic', 'handlers', 'cookie_sets', 'ikea_spb_mini.json'),
            'r'
        ))


class IkeaHandlerMSK(IkeaHandlerInterface):
    def get_handler_name(self) -> str:
        return "ikea_msk"

    def _get_cookie(self) -> List:
        return json.load(open(
            os.path.join('parser_app', 'logic', 'handlers', 'cookie_sets', 'ikea_msk_mini.json'),
            'r'
        ))
