from typing import List
from bs4 import BeautifulSoup
import time

from parser_app.logic.handlers.handler_interface import \
    HandlerInterface, ParsedProduct
from parser_app.logic.handlers.handler_tools import get_empty_parsed_product_dict
from parser_app.logic.handlers.tools import remove_odd_space


class LentaHandlerInterface(HandlerInterface):

    def __init__(self):
        super().__init__()

    def get_handler_name(self) -> str:
        raise NotImplemented('implement me! in sub class for needed city')

    def get_test_ulr(self) -> str:
        return r"https://lenta.com/"

    def _create_serch_url_for_category(self, category_row):
        return rf"https://lenta.com/search/?searchText={category_row['search_word']}"

    def _get_cookie(self) -> List:
        raise NotImplemented('implement me! in sub class for needed city')

    def _get_parsed_product_from_search(self, category_row) -> List[ParsedProduct]:

        if category_row['type'] != 'food':
            return []

        parsed_product_list = []

        url = self._create_serch_url_for_category(category_row)

        print(f"{self.get_handler_name()} -> {category_row['cat_title']}")
        self._driver.get(url)

        time.sleep(3.0)

        if 'товар не представлен' in str(self._driver.page_source):
            # FIXME error log
            print(f"no searched item in {self.get_handler_name()}, {category_row['cat_title']}")
            raise ValueError('no searched item in shop')

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        # with open(f"_{self.get_handler_name()}_{category_row['cat_title']}_{time.time()}.page_source", 'w+') as file:
        #     file.write(self._driver.page_source)
        # print(f"{category_row['cat_title']} len : {len(soup.find_all('div', class_='sku-card-small'))}")

        for page_item in soup.find_all('div', class_='sku-card-small'):
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
                url = page_item.find('a', class_='sku-card-small__link-block')['href']
                parsed_product['url'] = fr"https://lenta.com{url}"

                # price
                price_new = page_item.find('dd', class_='price__regular').text
                parsed_product['price_new'] = price_new

                float(remove_odd_space(parsed_product['price_new']).lower().replace(',', '.'))

                parsed_product['price_old'] = None
            except:
                print('ERROR! in parsing page_item')
                with open(f"_{self.get_handler_name()}_{category_row['cat_title']}_{time.time()}.page_item", 'w+') as file:
                    file.write(str(page_item))

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

            parsed_product_list.append(parsed_product)

        return parsed_product_list

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:

        self._driver.get(url)

        time.sleep(5.0)
        soup = BeautifulSoup(self._driver.page_source, 'html.parser')

        if 'В выбранном Вами магазине данный товар не представлен' in str(soup):
            # FIXME error log
            print('no searched item in shop')
            raise ValueError('no searched item in shop')

        parsed_product = get_empty_parsed_product_dict()
        parsed_product['url'] = url

        # title
        title = remove_odd_space(str(soup.find('div', class_='sku-card__title').text))
        try:
            sub_title = remove_odd_space(soup.find('div', class_='sku-card__sub-title').text)
            title += ' ' + sub_title
        except:
            # just no subtitle
            pass
        parsed_product['title'] = title

        # price
        for item in soup.find_all('div', class_='sku-card-params__item'):
            if 'обычная' in str(item).lower():
                price = remove_odd_space(item.find('dd', class_='price__regular').text).replace(' ', '')
                parsed_product['price_new'] = float(price.replace(',', '.'))

        # unit
        for item in soup.find_all('div', class_='sku-card-tab-params__item'):
            if 'Упаковка' in str(item):
                unit = remove_odd_space(item.find('dd', 'sku-card-tab-params__value').text)
                parsed_product['unit_title'] = unit

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
