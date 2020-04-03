from typing import List
import pandas as pd
from bs4 import BeautifulSoup
import time

from parser_app.logic.handlers.handler_interface import \
    HandlerInterface, ParsedProduct
from parser_app.logic.handlers.handler_tools import get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import wspex, find_float_number


class LentaHandler(HandlerInterface):

    def __init__(self):
        super().__init__()

    def get_handler_name(self) -> str:
        return 'lenta'

    def _create_serch_url_for_category(self, cat_title: str):
        return rf"https://lenta.com/search/?searchText={cat_title}"

    def _get_cookie(self) -> List:
        return []

    def _get_parsed_product_from_search(self, categoty_row) -> List[ParsedProduct]:

        if categoty_row['type'] != 'food':
            return []

        parsed_product_list = []

        url = self._create_serch_url_for_category(
            str(categoty_row['cat_title'])
        )
        print(f"{self.get_handler_name()} -> {categoty_row['cat_title']}")
        self._driver.get(url)

        time.sleep(3.0)

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        for page_item in soup.find_all('div', class_='sku-card-small'):
            parsed_product = get_empty_parsed_product_dict()

            # title
            title = page_item.find('div', class_='sku-card-small__title').text
            try:
                # sub title
                sub_title = page_item.find('div', class_='sku-card-small__sub-title').text
                title += ' ' + sub_title
            except:
                pass
            parsed_product['title'] = title

            # url
            url = page_item.find('a', class_='sku-card-small__link-block')['href']
            parsed_product['url'] = fr"https://lenta.com{url}"

            # price
            price_new = page_item.find('dd', class_='price__regular').text
            parsed_product['price_new'] = price_new
            parsed_product['price_old'] = None

            # here discount can be parsed
            # try:
            #     price_old = None
            #     for sub_price in page_item.find_all('div', class_='sku-card-params__item'):
            #
            #         if 'акц' in sub_price.find('dt', class_='sku-card-params__label').text:
            #             price_old = sub_price.find('dd', class_='price__primary').text
            #             print(price_old)
            #
            # except:
            #     pass

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:
        pass
