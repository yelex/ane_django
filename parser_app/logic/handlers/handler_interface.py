import os
import re
from typing import List, Dict, Union

import pandas as pd
from selenium import webdriver

from parser_app.logic.global_status import Global

ParsedProduct = Dict[str, Union[str, float, None]]


def get_empty_parsed_product_dict() -> ParsedProduct:
    return {
        # string, title from shop site
        'title': None,

        # string, url to product
        'url': None,

        # float, value in unit of unit_title
        'unit_value': None,

        # string, name of units
        'unit_title': None,

        # float, current price
        'price_new': None,

        # float, not none if offer detected and old price is available
        'price_old': None,
    }


def validate_ParsedProduct(parsed_product: ParsedProduct):
    assert isinstance(parsed_product, dict), "ParsedProduct must be dist"

    for key in ['title', 'url', 'unit_value', 'unit_title', 'price_new', 'price_old']:
        assert key in parsed_product.keys(), f"ParsedProduct must have this filed : {key}\n"\
                                             f"and you have {parsed_product}"

    for not_nan_key in ['title', 'url', 'price_new']:
        assert parsed_product[not_nan_key] is not None, \
            f"ParsedProduct must have this filed as non None : {not_nan_key}"\
            f"and you have {parsed_product}"

    assert type(parsed_product['title']) == str
    assert type(parsed_product['url']) == str
    assert type(parsed_product['unit_value']) == float or parsed_product['unit_value'] is None
    assert type(parsed_product['unit_title']) == str or parsed_product['unit_title'] is None
    assert type(parsed_product['price_new']) == float
    assert type(parsed_product['price_old']) == float or parsed_product['price_old'] is None


def get_empty_handler_DF() -> pd.DataFrame:
    """
    Create dataframe with preseted columns, this df will be used in extract_product function
    :return: pd.DataFrame
    """
    df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                               'site_title', 'price_new', 'price_old', 'site_unit',
                               'site_link', 'site_code'])
    return df


class HandlerInterface:

    # implement in every real handler
    def _get_handler_name(self) -> str:
        """
        :return: string, without spaces, represent current handler
        """
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_parsed_product_from_search(self, category) -> List[ParsedProduct]:
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:
        raise NotImplemented("Implement me! I'm just an interface!")

    # common part of handlers
    def __init__(self):
        self._old_urls: pd.DataFrame = pd.read_csv(self._get_path_to_old_urls())
        self._full_category_table: pd.DataFrame = pd.read_csv(
            os.path.join('parser_app', 'logic', 'description', 'category_with_keywords.csv')
        )
        self._full_category_table.fillna("")
        options = webdriver.ChromeOptions()
        self._driver = webdriver.Chrome(executable_path=Global().path_chromedriver, options=options)

    def _get_path_to_old_urls(self) -> str:
        """
        :return: str - path to file with tracked (old) urls for current handler
        """
        path = os.path.join('parser_app', 'logic', 'auto_detected_urls')
        if not os.path.exists(path):
            os.makedirs(path)

        path = os.path.join(path, f'{self._get_handler_name()}.csv')
        if not os.path.exists(path):
            df = pd.DataFrame(columns=['cat_title', 'title', 'url'])
            df.to_csv(path, index=False)
        return path

    def extract_products(self) -> pd.DataFrame:
        """
        Function (1) update url list for current handler, and then (2) create DataFrame from url list
        :return: pd.DataFrame with ???
        """
        try:
            print(f'Start update url list for {self._get_handler_name()}')
            self._update_url_list_from_search()
        except Exception as e:
            print(f"Some exception occur during searching for new urs in {self._get_handler_name()}")
            raise e

        try:
            print(f'Start create df bu url list {self._get_handler_name()}')
            return self._get_df_from_url_list()
        except Exception as e:
            print(f"Some exception occur during handling individual urls in {self._get_handler_name()}")
            raise e


    def _match_parsed_product(self, parsed_product: ParsedProduct, row) -> bool:
        """
        Return bool if row and parsed_product is equal.
        In a case of True, parsed_product will be ignored, as duplicated.
        Can be overrated by inheritance.

        :param parsed_product: ParsedProduct
        :param row: row from old urls file, contain 'category' - str, 'title' - str, 'url' - str
        :return: bool
        """
        return (
                parsed_product['title'] == row['title'] and
                parsed_product['url'] == row['url']
        )

    def _match_parsed_product_by_title(self, parsed_product: ParsedProduct, row) -> bool:
            """
            Return bool if row and parsed_product is equal.
            In a case of True url of row will be overrated by parsed_product url.
            Can be overrated by inheritance.

            :param parsed_product: ParsedProduct
            :param row: row from old urls file, contain 'category' - str, 'title' - str, 'url' - str
            :return: bool
            """
            return (
                    parsed_product['title'] == row['title']
            )

    def _update_category(self, parsed_item: ParsedProduct, cat_title: str):

        # try to update some old ones
        for _, row in self._old_urls[self._old_urls['cat_title'] == cat_title].iterrows():
            if self._match_parsed_product(parsed_item, row):
                return
            if self._match_parsed_product_by_title(parsed_item, row):
                row['url'] = parsed_item['url']
                return

        # if we have too few items in current category, add this item
        if len(self._old_urls[self._old_urls['cat_title'] == cat_title]) <= 15:
            self._old_urls = self._old_urls.append({
                    'cat_title': cat_title,
                    'title': parsed_item['title'],
                    'url': parsed_item['url'],
                },
                ignore_index=True,
            )

    def _update_url_list_from_search(self):
        for _, row in self._full_category_table.iterrows():

            parsed_list = self._get_parsed_product_from_search(row)

            for item in parsed_list:
                validate_ParsedProduct(item)

            for item in parsed_list:
                item['title'] = item['title'].lower()

                try:
                    if isinstance(row['keywords_cons'], str) and len(row['keywords_cons']) > 0:
                        if re.search(row['keywords_cons'], item['title']) is not None:
                            del item
                            continue
                    if isinstance(row['keywords_pro'], str) and len(row['keywords_pro']) > 0:
                        if re.search(row['keywords_pro'], item['title']) is None:
                            del item
                            continue
                except Exception as e:
                    print('\nsome re in keywords are uncorrect')
                    print(f"currently look at:\n"
                          f"keywords_cons: {row['keywords_cons']}\n"
                          f"keywords_cons type: {type(row['keywords_cons'])}\n"
                          f"keywords_pro: {row['keywords_pro']}\n"
                          f"keywords_pro type: {type(row['keywords_pro'])}\n"
                          f"parsed_product : {item}\n"
                          )

                self._update_category(item, row['cat_title'])

        self._old_urls.to_csv(self._get_path_to_old_urls(), index=False)

    def _get_df_from_url_list(self) -> pd.DataFrame:
        pass
