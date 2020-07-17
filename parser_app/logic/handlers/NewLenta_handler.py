from typing import List, Union
from bs4 import BeautifulSoup
import time

from parser_app.logic.handlers.handler_interface import HandlerInterface, ParsedProduct
from parser_app.logic.handlers.handler_tools import get_empty_parsed_product_dict
from parser_app.logic.handlers.handler_tools import remove_odd_space


class LentaHandlerInterface(HandlerInterface):

    def get_handler_name(self) -> str:
        raise NotImplemented('implement me! in sub class for needed city')

    def get_test_url(self) -> str:
        return r"https://lenta.com/"

    def _create_serch_url_for_category(self, category_row):
        return rf"https://lenta.com/search/?searchText={category_row['search_word']}"

    def _get_cookie(self) -> List:
        raise NotImplemented('implement me! in sub class for needed city')

    def _get_parsed_product_from_search(self, category_row) -> Union[None, List[ParsedProduct]]:
        if category_row['type'] != 'food':
            return None

        parsed_product_list = []

        url = self._create_serch_url_for_category(category_row)

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")

        page_source = self._load_page_with_TL(url, 10.0)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return []

        if 'товар не представлен' in str(page_source):
            # FIXME error log
            print(f"no searched item in {self.get_handler_name()}, {category_row['cat_title']}")
            raise ValueError('no searched item in shop')

        soup = BeautifulSoup(page_source, 'html.parser')

        for page_item in soup.find_all('div', class_='sku-card-small-container'):
            parsed_product = get_empty_parsed_product_dict()

            try:
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
                url = page_item.find('a', class_='sku-card-small')['href']
                parsed_product['url'] = fr"https://lenta.com{url}"

                # price
                price_new = page_item.find('span', class_='sku-price__integer').text
                parsed_product['price_new'] = price_new

                parsed_product['price_old'] = None

                parsed_product_list.append(parsed_product)
            except:
                print('ERROR! in parsing page_item')
                with open(f"_{self.get_handler_name()}_{category_row['cat_title']}_{time.time()}.page_item", 'w+') as file:
                    file.write(str(page_item))

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> Union[None, ParsedProduct]:

        page_source = self._load_page_with_TL(url, 10.0)
        if page_source is None:
            # fixme - log - fatal - can't load page
            print(f"can't load page, info:\n, handler : {self.get_handler_name()}\nurl: {url}")
            return None

        if 'В выбранном Вами магазине данный товар не представлен' in str(page_source):
            # FIXME error log
            print('no searched item in shop')
            raise ValueError('no searched item in shop')

        soup = BeautifulSoup(page_source, 'html.parser')

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

        # title
        title = remove_odd_space(str(soup.find('h1', class_='sku-page__title').text))
        try:
            sub_title = remove_odd_space(soup.find('div', class_='sku-page__sub-title').text)
            title += ' ' + sub_title
        except:
            pass
        parsed_product['title'] = title

        # price
        for item in soup.find_all('div', class_='sku-prices-block__item'):
            if 'обычная' in str(item).lower():
                price = remove_odd_space(item.find('span', class_='sku-price__integer').text).replace(' ', '')
                parsed_product['price_new'] = float(price.replace(',', '.'))

        # unit
        for item in soup.find_all('div', class_='sku-card-tab-params__item'):
            if 'Упаковка' in str(item):
                unit = remove_odd_space(item.find('dd', 'sku-card-tab-params__value').text)
                parsed_product['unparsed_units'] = unit

        return parsed_product


class LentaHandlerSPB(LentaHandlerInterface):
    def get_handler_name(self) -> str:
        return "lenta_spb"

    def _get_cookie(self) -> List:
        import json
        import os
        return json.load(open(
            os.path.join('.', 'parser_app', 'logic', 'handlers', 'cookie_sets', 'lenta_spb_mini.json'),
            'r'
        ))


class LentaHandlerMSK(LentaHandlerInterface):
    def get_handler_name(self) -> str:
        return "lenta_msk"

    def _get_cookie(self) -> List:
        import json
        import os
        return json.load(open(
            os.path.join('.', 'parser_app', 'logic', 'handlers', 'cookie_sets', 'lenta_msk_mini.json'),
            'r'
        ))
