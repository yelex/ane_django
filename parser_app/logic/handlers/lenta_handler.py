from typing import List
import pandas as pd
from bs4 import BeautifulSoup

from parser_app.logic.handlers.handler_interface import HandlerInterface, ParsedProduct, get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import wspex


class LentaSpbHandler(HandlerInterface):

    def __init__(self):
        super().__init__()

    def _get_handler_name(self) -> str:
        return 'lenta_handler'

    def _create_serch_url_for_category(self, cat_title: str):
        return rf"https://www.okeydostavka.ru/webapp/wcs/stores/servlet/SearchDisplay?categoryId=&storeId=10653&catalogId=12052&langId=-20&sType=SimpleSearch&resultCatEntryType=2&showResultsPage=true&searchSource=Q&pageView=&beginIndex=0&pageSize=72&searchTerm={cat_title}"

    def _get_parsed_product_from_search(self, categoty_row) -> List[ParsedProduct]:
        if categoty_row['type'] != 'food':
            return []

        parsed_product_list = []

        url = self._create_serch_url_for_category(
            str(categoty_row['cat_title']).replace(' ', '+')
        )
        print(f'url: {url}')
        self._driver.get(url)
        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        for product_list in soup.find_all('div', class_='product_listing_container'):
            for product_item in product_list.find_all('div', class_='product'):

                parsed_product = get_empty_parsed_product_dict()

                # title
                parsed_product['title'] = product_item.find('a')['title']

                # url
                parsed_product['url'] = rf"https://www.okeydostavka.ru/{product_item.find('a')['href']}"

                # in this case it absolutely unnecessary
                parsed_product['price_new'] = -1.0

                parsed_product_list.append(parsed_product)

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:
        self._driver.get(url)
        page = self._driver.page_source

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

        soup = BeautifulSoup(page, 'html.parser')

        # title
        parsed_product['title'] = soup.find('h1', class_='main_header').text

        # price
        price_item = soup.find('span', class_='product-price')
        price_new = wspex(price_item.find('span', class_='price').text)
        parsed_product['price_new'] = price_new

        try:
            price_old = wspex(price_item.find('span', class_='crossed').text)
            parsed_product['price_old'] = price_old
        except:
            # we just have now any discount
            pass

        # units
        unit_item = soup.find('ul', class_='widget-list').find_all('li', class_='attributes__item')[1]
        unit_title = wspex(unit_item.find('div', class_='attributes__name').text)
        parsed_product['unit_title'] = unit_title

        unit_value = wspex(unit_item.find('div', class_='attributes__value').text)
        parsed_product['unit_value'] = unit_value

        return parsed_product
