import time
from typing import List, Optional, Union

from bs4 import BeautifulSoup
from selenium import webdriver

from parser_app.logic.handlers.handler_interface import HandlerInterface
from parser_app.logic.handlers.handler_tools import ParsedProduct, get_empty_parsed_product_dict, remove_non_digits
from parser_app.logic.handlers.handler_tools import remove_odd_space, remove_ALL_spaces


class EldoradoHandlerInterface(HandlerInterface):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self._category_links = pd.da

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

    def get_test_url(self) -> str:
        return rf"https://www.eldorado.ru"

    def create_general_search_url(self, search_word: str, page_num: Optional[int] = None) -> str:
        if page_num is None or page_num == 1 or page_num == 0:
            return rf"https://www.eldorado.ru/search/catalog.php?q={search_word.replace(' ', '+')}&utf"
        return rf"https://www.eldorado.ru/search/catalog.php?" \
               rf"PAGEN_SEARCH={page_num}&q={search_word.replace(' ', '+')}&utf"

    def _get_parsed_product_from_search(self, category_row) -> Union[None, List[ParsedProduct]]:
        if category_row['sub_type'] != 'appliances':
            return None

        full_parsed_product_list = []

        for page_num in range(1):
            parsed_product_list = []
            # url = self.get_search_url_for_category(category_row, page_num)
            url = self.create_general_search_url(category_row['search_word'], page_num)

            print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
            print(f'using url:\n{url}')

            page_source = self._load_page_with_TL(url)
            if page_source is None:
                # fixme - log - fatal - can't load page
                print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
                return None

            soup = BeautifulSoup(page_source, 'html.parser')

            for parsed_item in soup.find_all('li', {'data-dy': 'product'}):
                parsed_product = get_empty_parsed_product_dict()
                # title
                title = remove_odd_space(parsed_item.find('a', {'data-dy': 'title'}).text)
                parsed_product['title'] = title

                # url
                url = remove_odd_space(parsed_item.find('a', {'data-dy': 'title'})['href'])
                url = f"https://www.eldorado.ru{url}"
                parsed_product['url'] = url

                # price
                price_list = []
                for price_item in parsed_item.find_all('span'):
                    if hasattr(price_item, 'text') and price_item.text[-2:] == 'р.':
                        mb_price = int(remove_non_digits(price_item.text))
                        if 100 <= mb_price <= 100000:
                            price_list.append(mb_price)
                price = sorted(price_list)[-1]
                parsed_product['price_new'] = price

                parsed_product_list.append(parsed_product)
            full_parsed_product_list.extend(parsed_product_list)
        return full_parsed_product_list

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
