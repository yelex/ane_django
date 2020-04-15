import os
import re
from typing import List, Set
from datetime import datetime
import pandas as pd
from selenium import webdriver

from parser_app.logic.global_status import get_usual_webdriver
from parser_app.logic.handlers.handler_tools import \
    ParsedProduct, \
    get_empty_handler_DF, \
    validate_ParsedProduct, \
    postprocess_parsed_product
from parser_app.logic.proxy_tools.common_proxy_testers import simple_test_driver_with_url
from parser_app.logic.proxy_tools.proxy_keeper import ProxyKeeper


class HandlerInterface:

    # implement in every real handler
    def get_handler_name(self) -> str:
        """
        :return: string, without spaces, represent current handler
        """
        raise NotImplemented("Implement me! I'm just an interface!")

    def test_web_driver(self, driver: webdriver.Chrome) -> bool:
        """
        This function should test webdriver for suit this concrete site handler
        This can be not changed in real handlers, cause there are simple test to connections.

        :param driver: webdriver.Chrome
        :return: True if cat use
        """
        return True

    def get_test_ulr(self) -> str:
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_parsed_product_from_search(self, category) -> List[ParsedProduct]:
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_parsed_product_from_url(self, url) -> ParsedProduct:
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_cookie(self) -> List:
        return []

    # common part of handlers
    def __init__(self):
        self._old_urls: pd.DataFrame = pd.read_csv(self._get_path_to_old_urls())
        self._full_category_table: pd.DataFrame = pd.read_csv(
            os.path.join('parser_app', 'logic', 'description', 'category_with_keywords.csv')
        )
        self._full_category_table.fillna("")

        # setup final df
        self._returned_df: pd.DataFrame = get_empty_handler_DF()
        self._title_done: Set[str] = set()

    def _create_webdriver(self):
        proxy_keeper = ProxyKeeper()
        try:
            driver = proxy_keeper.get_proxy_for_site(self)
        except:
            # FIXME fatal log
            print(f"can't create proxy for {self.get_handler_name()}")
            driver = get_usual_webdriver()
            if not self.test_web_driver(driver) or not simple_test_driver_with_url(driver, self.get_test_ulr()):
                # FIXME fatal log
                print(f"can't create usual driver for {self.get_handler_name()}")
                driver.quit()
                raise ValueError(f"can't use any driver for {self.get_handler_name()}")

        self._driver = driver

        if len(self._get_cookie()) != 0:
            # need to make single load

            self._driver.get(self.get_test_ulr())

            for cookie in self._get_cookie():
                self._driver.add_cookie(cookie)

            # FIXME susses log

    def _get_path_to_old_urls(self) -> str:
        """
        :return: str - path to file with tracked (old) urls for current handler
        """
        path = os.path.join('parser_app', 'logic', 'auto_detected_urls')
        if not os.path.exists(path):
            os.makedirs(path)

        path = os.path.join(path, f'{self.get_handler_name()}.csv')
        if not os.path.exists(path):
            df = pd.DataFrame(columns=['cat_title', 'title', 'url'])
            df.to_csv(path, index=False)
        return path

    def extract_products(self) -> pd.DataFrame:
        """
        Call this function to get df with data.

        Try create webdriver (0), if fails return empty pd.DataFrame
        Function (1) update url list for current handler,
        and then (2) create DataFrame from url list
        :return: pd.DataFrame with ???
        """
        try:
            # setup driver
            self._create_webdriver()
        except:
            # FIXME fatal log
            print(f"can't create driver for {self.get_test_ulr()}, return empty pd.DataFrame")
            return get_empty_handler_DF()

        try:
            print(f'Start update url list for {self.get_handler_name()}')
            self._update_url_list_from_search()
        except Exception as e:
            print(f"Some exception occur during searching for new urs in {self.get_handler_name()}")
            self._driver.quit()
            raise e

        try:
            print(f'Start create df by url list {self.get_handler_name()}')
            self._get_df_from_url_list()
        except Exception as e:
            print(f"Some exception occur during handling individual urls in {self.get_handler_name()}")
            self._driver.quit()
            raise e

        self._driver.quit()
        return self._returned_df

    def _add_df_row_from_parsed_product(self, parsed_product: ParsedProduct, category_row) -> None:
        if parsed_product['title'] in self._title_done:
            return
        self._title_done.add(parsed_product['title'])

        self._returned_df = self._returned_df.append({
                'date': datetime.now().strftime("%Y-%m-%d"),
                'type': category_row['type'],
                'category_id': int(category_row['id']),
                'category_title': category_row['cat_title'],
                'site_title': parsed_product['title'],
                'price_new': parsed_product['price_new'],
                'price_old': parsed_product['price_old'],
                'site_unit': '1кг',
                'site_link': parsed_product['url'],
                'site_code': self.get_handler_name(),
            },
            ignore_index=True,
        )

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
            return parsed_product['title'] == row['title']

    def _update_category(self, parsed_item: ParsedProduct, category_row):
        # try to update some old ones
        for _, row in self._old_urls[
            self._old_urls['cat_title'] == category_row['cat_title']
        ].iterrows():
            if self._match_parsed_product(parsed_item, row):
                self._add_df_row_from_parsed_product(parsed_item, category_row)
                return
            if self._match_parsed_product_by_title(parsed_item, row):
                row['url'] = parsed_item['url']
                self._add_df_row_from_parsed_product(parsed_item, category_row)
                return

        # if we have too few items in current category, add this item
        if len(self._old_urls[self._old_urls['cat_title'] == category_row['cat_title']]) <= 15:
            print(f"add new Item to category {category_row['cat_title']}, it is {parsed_item['title']}")
            self._old_urls = self._old_urls.append({
                    'cat_title': category_row['cat_title'],
                    'title': parsed_item['title'],
                    'url': parsed_item['url'],
                },
                ignore_index=True,
            )
            self._add_df_row_from_parsed_product(parsed_item, category_row)

    def _update_url_list_from_search(self):
        for _, category_row in self._full_category_table.iterrows():

            try:
                parsed_list = self._get_parsed_product_from_search(category_row)
            except:
                # FIXME fatal log
                print(f'Error while handling search result for:\n'
                      f'handler : {self.get_handler_name()};\n'
                      f'category : {category_row["cat_title"]}')
                continue

            for item in parsed_list:
                postprocess_parsed_product(item)
                validate_ParsedProduct(item)

                try:
                    if isinstance(category_row['keywords_cons'], str) and\
                            len(category_row['keywords_cons']) > 0:
                        if re.search(category_row['keywords_cons'], item['title']) is not None:
                            # print(f'del item due to  keywords_cons {item["title"]}')
                            del item
                            continue
                    if isinstance(category_row['keywords_pro'], str) and\
                            len(category_row['keywords_pro']) > 0:
                        if re.search(category_row['keywords_pro'], item['title']) is None:
                            # print(f'del item due to  keywords_pro {item["title"]}')
                            del item
                            continue
                except Exception as e:
                    print('\nsome re in keywords are uncorrect')
                    print(f"currently look at:\n"
                          f"keywords_cons: {category_row['keywords_cons']}\n"
                          f"keywords_cons type: {type(category_row['keywords_cons'])}\n"
                          f"keywords_pro: {category_row['keywords_pro']}\n"
                          f"keywords_pro type: {type(category_row['keywords_pro'])}\n"
                          f"parsed_product : {item}\n"
                          )

                self._update_category(item, category_row)

        self._old_urls.to_csv(self._get_path_to_old_urls(), index=False)

    def _get_df_from_url_list(self) -> None:
        for index, url_row in self._old_urls.iterrows():
            # have columns : 'cat_title', 'title', 'url'

            if url_row['title'] in self._title_done:
                # was possessed
                continue

            try:
                parsed_product: ParsedProduct = self._get_parsed_product_from_url(url_row['url'])
                postprocess_parsed_product(parsed_product)
                validate_ParsedProduct(parsed_product)
            except:
                print(f'in parser {self.get_handler_name()} Error during parsing single item:')
                print(url_row['cat_title'])
                print(url_row['title'])
                print(url_row['url'], end='\n\n')

                continue

            parsed_product = postprocess_parsed_product(parsed_product)

            print(parsed_product)

            self._add_df_row_from_parsed_product(
                parsed_product,
                self._full_category_table[self._full_category_table['cat_title'] == url_row['cat_title']].iloc[0],
            )
