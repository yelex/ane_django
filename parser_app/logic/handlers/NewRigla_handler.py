from typing import List
from bs4 import BeautifulSoup
import time

from selenium import webdriver

from parser_app.logic.handlers.handler_interface import HandlerInterface, ParsedProduct
from parser_app.logic.handlers.handler_tools import get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import remove_odd_space, remove_ALL_spaces


class RiglaHandlerInterface(HandlerInterface):

    def __init__(self):
        super().__init__()

    def get_handler_name(self) -> str:
        raise NotImplemented

    def get_test_ulr(self) -> str:
        return r"https://rigla.ru/"

    def test_web_driver(self, driver: webdriver.Chrome) -> bool:
        return True

    def _create_search_url_for_category(self, name: str) -> str:
        raise NotImplemented

    def _create_link_to_product(self, product_url: str) -> str:
        raise NotImplemented

    def _get_cookie(self) -> List:
        """No cookie, for Rigla just url to change city"""
        return []

    def _get_parsed_product_from_search(self, category_row) -> List[ParsedProduct]:
        if category_row['sub_type'] != 'medicine':
            return []

        parsed_product_list = []

        url = self._create_search_url_for_category(category_row['search_word'])

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        print(f'using url:\n{url}')

        self._driver.get(url)

        time.sleep(6.0)

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        for parsed_item in soup.find_all('div', class_='product'):
            try:
                parsed_product = get_empty_parsed_product_dict()
                # title
                title = remove_odd_space(parsed_item.find('a', class_='product__title').text)
                sub_title = remove_odd_space(parsed_item.find('a', class_='product-brand__link').text)
                title += ' ' + sub_title
                parsed_product['title'] = title

                # url
                url = parsed_item.find('a', class_='product__title')['href']
                parsed_product['url'] = self._create_link_to_product(url)

                # price
                price = remove_ALL_spaces(parsed_item.find('span', class_='product__active-price-number').text)
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
        title = remove_odd_space(soup.find('h1', class_='product-cart__title').text)
        sub_title = remove_odd_space(soup.find('a', class_='product-cart__content-info-header-black').text)
        title += ' ' + sub_title
        parsed_product['title'] = title

        # price
        price = remove_ALL_spaces(soup.find('div', class_='product-cart__content-price-actual').text)[:-1]
        parsed_product['price_new'] = price

        return parsed_product


class RiglaHandlerMSK(RiglaHandlerInterface):
    def get_handler_name(self) -> str:
        return "rigla_msk"

    def _create_search_url_for_category(self, name: str) -> str:
        return f"https://www.rigla.ru/search/{name}"

    def _create_link_to_product(self, product_url: str) -> str:
        return f"https://www.rigla.ru{product_url}"


class RiglaHandlerSPB(RiglaHandlerInterface):
    def get_handler_name(self) -> str:
        return "rigla_spb"

    def _create_search_url_for_category(self, name: str) -> str:
        return f"https://spb.rigla.ru/search/{name}"

    def _create_link_to_product(self, product_url: str) -> str:
        return f"https://spb.rigla.ru{product_url}"
