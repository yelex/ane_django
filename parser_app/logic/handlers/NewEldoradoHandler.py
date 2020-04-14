import time
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver

from parser_app.logic.handlers.handler_interface import HandlerInterface
from parser_app.logic.handlers.handler_tools import ParsedProduct, get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import remove_odd_space, remove_ALL_spaces


class EldoradoHandlerInterface(HandlerInterface):

    # implement in every real handler
    def get_handler_name(self) -> str:
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
        return rf"https://www.eldorado.ru"

    def _create_serch_url_for_category(self, name: str) -> str:
        return rf"https://www.eldorado.ru/search/catalog.php?q={name.replace(' ', '+')}&utf"

    def _get_parsed_product_from_search(self, category_row) -> List[ParsedProduct]:

        if category_row['sub_type'] != 'appliances':
            return []

        parsed_product_list = []

        url = self._create_serch_url_for_category(str(category_row['search_word']))

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        print(f'using url:\n{url}')

        self._driver.get(url)

        time.sleep(6.0)

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        for parsed_item in soup.find_all('div', class_='item'):
            try:
                parsed_product = get_empty_parsed_product_dict()
                # title
                title = remove_odd_space(parsed_item.find('div', class_='itemTitle').text)
                parsed_product['title'] = title

                # url
                url = remove_odd_space(parsed_item.find('div', class_='itemTitle').find('a')['href'])
                url = f"https:{url}"
                parsed_product['url'] = url

                # price
                try:
                    price = remove_odd_space(parsed_item.find('span', class_='old-price').text).replace(' ', '')[:-2]
                except:
                    price = remove_odd_space(parsed_item.find('span', class_='itemPrice').text).replace(' ', '')[:-2]
                parsed_product['price_new'] = price
                parsed_product['price_old'] = None

                # float, value in unit of unit_title
                parsed_product['unit_value'] = 1
                # string, name of units
                parsed_product['unit_title'] = '1шт'

                parsed_product_list.append(parsed_product)
            except:
                pass
        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:

        self._driver.get(url)

        time.sleep(5.0)
        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url
        # title
        title = remove_odd_space(soup.find('h1', class_='catalogItemDetailHd', itemprop='name').text)
        parsed_product['title'] = title

        # price
        try:
            price = remove_ALL_spaces(soup.find('span', class_='product-box-price__old-el').text)[:-2]
        except:
            price = remove_ALL_spaces(soup.find('div', class_='product-box-price__active').text)[:-2]
        parsed_product['price_new'] = price
        parsed_product['price_old'] = None

        # float, value in unit of unit_title
        parsed_product['unit_value'] = 1
        # string, name of units
        parsed_product['unit_title'] = '1шт'

        return parsed_product

    def _get_cookie(self) -> List:
        raise NotImplemented


class EldoradoHandlerMSK(EldoradoHandlerInterface):
    def get_handler_name(self) -> str:
        return 'eldorado_msk'

    def _get_cookie(self) -> List:
        import json
        import os
        return json.load(open(
            os.path.join('parser_app', 'logic', 'handlers', 'cookie_sets', 'eldorado_msk_mini.json'),
            'r'
        ))


class EldoradoHandlerSPB(EldoradoHandlerInterface):
    def get_handler_name(self) -> str:
        return 'eldorado_spb'

    def _get_cookie(self) -> List:
        import json
        import os
        return json.load(open(
            os.path.join('parser_app', 'logic', 'handlers', 'cookie_sets', 'eldorado_spb_mini.json'),
            'r'
        ))
