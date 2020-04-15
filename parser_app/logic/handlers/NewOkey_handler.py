from typing import List
import pandas as pd
from bs4 import BeautifulSoup
import time

from selenium import webdriver

from parser_app.logic.handlers.handler_interface import \
    HandlerInterface, ParsedProduct
from parser_app.logic.handlers.handler_tools import get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import wspex, find_float_number


class OkeySpbHandler(HandlerInterface):

    def __init__(self):
        super().__init__()

    def get_handler_name(self) -> str:
        return 'okey_spb'

    def get_test_ulr(self) -> str:
        return r"https://www.okeydostavka.ru/spb"

    def test_web_driver(self, driver: webdriver.Chrome) -> bool:
        return True

    def _create_serch_url_for_category(self, cat_title: str):
        return rf"https://www.okeydostavka.ru/webapp/wcs/stores/servlet/SearchDisplay?categoryId=&storeId=10653&catalogId=12052&langId=-20&sType=SimpleSearch&resultCatEntryType=2&showResultsPage=true&searchSource=Q&pageView=&beginIndex=0&pageSize=72&searchTerm={cat_title}"

    def _get_parsed_product_from_search(self, categoty_row) -> List[ParsedProduct]:
        if categoty_row['type'] != 'food':
            return []

        parsed_product_list = []

        url = self._create_serch_url_for_category(
            str(categoty_row['cat_title']).replace(' ', '+')
        )

        print(f"{self.get_handler_name()} -> {categoty_row['cat_title']}")
        print(f'using url:\n{url}')

        self._driver.get(url)

        time.sleep(6.0)

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        for product_list in soup.find_all('div', class_='product_listing_container'):
            for product_item in product_list.find_all('div', class_='product'):
                try:
                    parsed_product = get_empty_parsed_product_dict()

                    # title
                    parsed_product['title'] = product_item.find('a')['title']

                    # url
                    parsed_product['url'] = rf"https://www.okeydostavka.ru{product_item.find('a')['href']}"

                    try:
                        parsed_product['unit_value'] = find_float_number(
                            product_item.find('div', class_='product-weight').text
                        )
                        parsed_product['unit_title'] = wspex(product_item.find('div', class_='product-weight').find('span').text)
                    except:
                        parsed_product['unit_value'] = None
                        parsed_product['unit_title'] = None

                    # price, also work for reduced price
                    product_item_price = product_item.find('div', class_='product-price')
                    parsed_product['price_new'] = find_float_number(
                        product_item_price.find('span', class_='price').text
                    )
                    # price, old (not reduced)
                    try:
                        old_price = wspex(
                            product_item_price.find('span', class_='crossed').text
                        )
                        parsed_product['price_old'] = find_float_number(old_price)
                    except:
                        # just no discount
                        parsed_product['price_old'] = None
                        pass

                    parsed_product_list.append(parsed_product)
                except:
                    print('\nLenta parser, cant parse:')
                    print(product_item, end='\n\n')

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:
        self._driver.get(url)

        time.sleep(5.0)

        page = self._driver.page_source

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

        soup = BeautifulSoup(page, 'html.parser')

        print(f'temp_{time.time()}.soup')

        with open(f'temp_{time.time()}.soup', 'w') as file:
            file.write(str(soup))

        # title
        parsed_product['title'] = soup.find('h1', class_='main_header').text

        # price
        price_item = soup.find('span', class_='product-price')
        price_new = find_float_number(price_item.find('span', class_='price').text)
        parsed_product['price_new'] = price_new

        try:
            price_old = find_float_number(price_item.find('span', class_='crossed').text)
            parsed_product['price_old'] = price_old
        except:
            # we just have now any discount
            parsed_product['price_old'] = None
            pass

        # units
        try:
            unit_item = soup.find('ul', class_='widget-list').find_all('li', class_='attributes__item')[1]
            unit_title = wspex(unit_item.find('div', class_='attributes__name').text)
            parsed_product['unit_title'] = unit_title

            unit_value = find_float_number(unit_item.find('div', class_='attributes__value').text)
            parsed_product['unit_value'] = unit_value
        except:
            pass

        return parsed_product
