import time
from typing import List, Union

from bs4 import BeautifulSoup
from selenium import webdriver

from anehome.settings import DEVELOP_MODE
from parser_app.logic.handlers.handler_interface import HandlerInterface
from parser_app.logic.handlers.handler_tools import ParsedProduct, get_empty_parsed_product_dict
from parser_app.logic.handlers.handler_tools import remove_odd_space


class PerekrestokInterfaceHandler(HandlerInterface):
    '''
    Interface for all Perekrestok parsers, for needed city implement name function and cookie
    '''

    # implement in every real handler
    def get_handler_name(self) -> str:
        raise NotImplemented

    def _get_cookie(self) -> List:
        raise NotImplemented

    def test_web_driver(self, driver: webdriver.Chrome) -> bool:
        """
        This function should test webdriver for suit this concrete site handler
        This can be not changed in real handlers, cause there are simple test to connections.

        :param driver: webdriver.Chrome
        :return: True if cat use
        """
        return True

    def get_test_ulr(self) -> str:
        return r"https://www.perekrestok.ru/"

    def _create_serch_url_for_category(self, name: str) -> str:
        return rf"https://perekrestok.ru/catalog/search?text={name}"

    def _get_parsed_product_from_search(self, category_row) -> Union[None, List[ParsedProduct]]:
        if category_row['type'] != 'food':
            return None

        parsed_product_list = []

        url = self._create_serch_url_for_category(
            str(category_row['search_word'])
        )

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        print(f'using url:\n{url}')

        page_source = self._load_page_with_TL(url)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return None

        soup = BeautifulSoup(page_source, 'html.parser')

        for parsed_item in soup.find_all('li', class_='xf-catalog__item'):

            if "Временно отсутствует" in str(parsed_item):
                continue

            parsed_product = get_empty_parsed_product_dict()

            # title
            title = remove_odd_space(parsed_item.find('a', class_='xf-product-title__link').text)
            parsed_product['title'] = title

            # url
            url = parsed_item.find('a', class_='xf-product-title__link')['href']
            url = f"https://perekrestok.ru{url}"
            parsed_product['url'] = url

            # price
            try:
                price = parsed_item.find('div', class_='xf-product-cost__old-price')['data-cost']
            except:
                price = parsed_item.find('div', class_='xf-product-cost__current')['data-cost']
            parsed_product['price_new'] = price

            parsed_product_list.append(parsed_product)

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
        title = remove_odd_space(soup.find('h1', class_='xf-product-card__title').text)
        parsed_product['title'] = title

        # price
        price_item = soup.find('div', class_='xf-product-card__product-buy')
        try:
            price = price_item.find('div', class_='js-product__old-cost')['data-cost']
        except:
            price = price_item.find('div', class_='xf-product-cost__current')['data-cost']
        parsed_product['price_new'] = price

        return parsed_product


class PerekrestokHandlerSPB(PerekrestokInterfaceHandler):

    def get_handler_name(self) -> str:
        return 'perekrestok_spb'

    def _get_cookie(self) -> List:
        import json
        import os
        return json.load(open(
            os.path.join('parser_app', 'logic', 'handlers', 'cookie_sets', 'perekrestok_spb_mini.json'),
            'r'
        ))
