import os
import re
import time
from typing import List, Set, Union, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import requests
from selenium import webdriver
from tbselenium.tbdriver import TorBrowserDriver

from anehome.settings import DEVELOP_MODE
from parser_app.logic.global_status import get_usual_webdriver, create_tor_service_browser
from parser_app.logic.handlers.handler_tools import \
    ParsedProduct, \
    get_empty_handler_DF, \
    validate_ParsedProduct, \
    postprocess_parsed_product, \
    load_page_with_TL, cookie_to_name_value
from parser_app.logic.proxy_tools.common_proxy_testers import simple_test_driver_with_url, test_html_page
from parser_app.logic.proxy_tools.proxy_keeper import ProxyKeeper
from parser_app.logic.tor_utils import restart_tor
from parser_app.logic.tor_service_settings import TOR_SERVICE_PORT, TOR_SERVICE_HOST

"""
If Interface_TEST_MODE enabled (set True) then HandlerInterface will fetch only one item from search
and only one item from stored urls. In order just to test if all shop handlers work.  
"""
Interface_TEST_MODE: bool = True
if not DEVELOP_MODE:
    Interface_TEST_MODE = False


class HandlerInterface:
    # actually, doesn't used for now
    # MAX_PAGES_OF_SEARCH_TO_PROCESS: int = 5

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

    def get_test_url(self) -> str:
        """
        Return single string - url of shop.
        Fro example 'http://ikea.com'

        :return: string
        """
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_parsed_product_from_search(self, category) -> Union[None, List[ParsedProduct]]:
        """
        Return list of items for category. Using shop search line.

        :param category: row from category_with_keywords.csv
        :return: None if this category not for current handler, list of ParsedProduct otherwise
        """
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_parsed_product_from_url(self, url: str) -> Union[None, ParsedProduct]:
        """
        Get single ParsedProduct item connected with url.

        :param url: string url of item
        :return: ParsedProduct or None if trouble with page loading
        """
        raise NotImplemented("Implement me! I'm just an interface!")

    def _get_cookie(self) -> List[Dict[str, Any]]:
        """
        It can be useful for some shope implement all function of parsing independently of city.
        And then inherit parser for city with changing just name and cookie sets.

        :return: list of dicts == list of cookie to use
        """
        return []

    # common part of handlers
    def __init__(
            self,
            proxy_method: str = 'tor-service',
            use_request: bool = False,
            tor_driver: Optional[TorBrowserDriver] = None,
    ):
        assert proxy_method in ['tor-service', 'tor-browser', 'find-proxy', 'no-proxy'], \
            "proxy_method must be one of '['tor-service', 'tor-browser', 'find-proxy', 'no-proxy']'"

        assert not use_request or proxy_method in ['tor-service', 'find-proxy', 'no-proxy'], \
            "you should use 'use_request' only with '['tor-service', 'find-proxy', 'no-proxy']'"

        assert proxy_method != 'tor-browser' or tor_driver is not None, \
            "you must pass 'tor_driver' if you set proxy_method as 'tor-browser'"

        self._use_request = use_request
        self._request_proxy = {}
        self._tor_driver = tor_driver
        self._set_up_proxy(proxy_method)

        # self._url_getter: URLGetterInterface = url_getter
        self._old_urls: pd.DataFrame = pd.read_csv(self._get_path_to_old_urls())

        self._full_category_table: pd.DataFrame = pd.read_csv(
            os.path.join('parser_app', 'logic', 'description', 'category_with_keywords.csv')
        )
        self._full_category_table.fillna("")

        # setup final df
        self._returned_df: pd.DataFrame = get_empty_handler_DF()
        self._url_done: Set[str] = set()

    def _set_up_proxy(self, proxy_method: str) -> None:

        if self._use_request:
            if proxy_method == 'no-proxy':
                self._request_proxy = {}
                return
            if proxy_method == 'tor-service':
                self._request_proxy = {
                    'SOCKSv5': f"{TOR_SERVICE_HOST}:{TOR_SERVICE_PORT}",
                }
            if proxy_method == 'find-proxy':
                raise NotImplemented('I hope you wont use this function')

        # 4 proxy cases
        if proxy_method == 'no-proxy' or proxy_method is None:
            # case 1 - do not use proxy
            self._driver = get_usual_webdriver()
        elif proxy_method == 'tor-browser':
            # case 2 - use tor browser from init
            self._setup_tor_driver()
        elif proxy_method == 'tor-service':
            # case 3 - connect via running tor service
            # NOTE, need root to restart tor
            test_times = 0
            while True:

                self._driver = create_tor_service_browser()

                if simple_test_driver_with_url(self._driver, self.get_test_url()):
                    break

                restart_tor()
                test_times += 1

                if test_times >= 3:
                    raise ValueError(f"can't fetch {self.get_test_url()} via TOR service")
        elif proxy_method == 'find-proxy':
            # case 4 - search for proxy in installed sites
            try:
                self._create_webdriver()
            except Exception as e:
                # FIXME fatal log
                print(f"can't create driver for {self.get_test_url()}, return empty pd.DataFrame")
                print(e.__str__())
                self._driver = None
                self._tor_driver = None

    def _load_page_with_TL(self, page_url, time_limit: float = 3.5) -> Union[str, None]:
        """
        Base method for page loading.
        Return string - page source if page load in time_limit second,
            otherwise return any loaded string,
            else return None
        """
        if self._use_request:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(
                page_url,
                timeout=time_limit,
                cookies=cookie_to_name_value(self._get_cookie()),
                headers=headers,
                proxies=self._request_proxy,
            )
            page_source = response.text
            if not test_html_page(page_source):
                return None
            return page_source

        if self._tor_driver is not None:
            # load_page_with_TL(self._tor_driver, page_url, time_limit)
            self._tor_driver.load_url(page_url, wait_for_page_body=True)
            time.sleep(time_limit)
            return self._tor_driver.page_source

        return load_page_with_TL(self._driver, page_url, time_limit)

    def _setup_tor_driver(self) -> None:
        assert isinstance(self._tor_driver, TorBrowserDriver)
        self._tor_driver.load_url(self.get_test_url())

        for cookie in self._get_cookie():
            self._tor_driver.add_cookie({
                "name": cookie["name"],
                "value": cookie["value"],
            })

    def _quiet_driver(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except:
                pass

    def _create_webdriver(self) -> None:
        if self._tor_driver is not None:
            self._setup_tor_driver()
            return

        proxy_keeper = ProxyKeeper()
        try:
            driver = proxy_keeper.get_web_driver_for_site(self)
        except:
            # FIXME fatal log
            print(f"can't create proxy for {self.get_handler_name()}, try to create usual driver")
            driver = get_usual_webdriver()
            if not self.test_web_driver(driver) or not simple_test_driver_with_url(driver, self.get_test_url()):
                # FIXME fatal log
                print(f"can't create usual driver for {self.get_handler_name()}")
                try:
                    driver.quit()
                except:
                    pass
                raise ValueError(f"can't use any driver for {self.get_handler_name()}")

        self._driver = driver

        if len(self._get_cookie()) != 0:
            # need to make single load
            if DEVELOP_MODE:
                print(f'Start to add cookie for {self.get_handler_name()}')

            test_page = self._load_page_with_TL(self.get_test_url(), 10.0)
            if test_page is None:
                print(f"problem with loading page on handler : {self.get_handler_name()}")
                raise ValueError(
                    f"can't set cookie, cause of problem with first loading, "
                    f"parser : {self.get_handler_name()}"
                )

            for cookie in self._get_cookie():
                self._driver.add_cookie({
                    "name": cookie["name"],
                    "value": cookie["value"],
                    # "domain": domain,
                })

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

        Function (1) update url list for current handler,
        and then (2) create DataFrame from url list
        :return: pd.DataFrame with ???
        """
        if self._driver is None and self._tor_driver is None:
            print(f"Can't fetch {self.get_handler_name()}, no web driver")
            print(f"return empty DF in order to not interapt all process")
            return get_empty_handler_DF()

        try:
            print(f'Start update url list for {self.get_handler_name()}')
            self._update_url_list_from_search()
        except Exception as e:
            print(f"Some exception occur during searching for new urs in {self.get_handler_name()}")
            self._quiet_driver()
            raise e

        try:
            print(f'Start create df by url list {self.get_handler_name()}')
            self._get_df_from_url_list()
        except Exception as e:
            print(f"Some exception occur during handling individual urls in {self.get_handler_name()}")
            self._quiet_driver()
            raise e

        try:
            self._quiet_driver()
        except:
            pass

        return self._returned_df

    def _add_df_row_from_parsed_product(self, parsed_product: ParsedProduct, category_row) -> None:
        """
        We should update each product ones a launch. So we will store list of already updated products.

        :param parsed_product: product to update
        :param category_row: category row to update
        :return: nothing
        """
        if parsed_product['url'] in self._url_done:
            return
        self._url_done.add(parsed_product['url'])

        self._returned_df = self._returned_df.append({
                'date': datetime.now().strftime("%Y-%m-%d"),
                'type': category_row['type'],
                'category_id': int(category_row['id']),
                'category_title': category_row['cat_title'],
                'site_title': parsed_product['title'],
                'price_new': parsed_product['price_new'],
                'price_old': parsed_product['price_old'],
                'site_unit': parsed_product['unit_title'] + str(parsed_product['unit_value']),
                'site_link': parsed_product['url'],
                'site_code': self.get_handler_name(),
                'miss': False,
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

    def _match_parsed_product_by_url(self, parsed_product: ParsedProduct, row) -> bool:
            """
            Return bool if row and parsed_product is equal.
            In a case of True url of row will be overrated by parsed_product url.
            Can be overrated by inheritance.

            :param parsed_product: ParsedProduct
            :param row: row from old urls file, contain 'category' - str, 'title' - str, 'url' - str
            :return: bool
            """
            return parsed_product['url'] == row['url']

    def _update_category(self, parsed_item: ParsedProduct, category_row):
        """
        This function try to update stored list of items (= products).
        I use this logic:
         - firstly we look at url and title of new item,
            if them absolutely equal to some old one we just ignore this new item
         - else, if only url is the same as some old ulr, I consider that title of item is updated
         - else, I consider new item to be really new, so if I haven't enough items in this category
            I add new item to stored list

        :param parsed_item: new item
        :param category_row: new item's category
        :return: nothing
        """
        print(f"{category_row['cat_title']} ->\n"
              f" title: {parsed_item['title']}, price : {parsed_item['price_new']}, "
              f"units: {parsed_item['unit_title']} {parsed_item['unit_value']}")

        # try to update some old ones
        for _, row in self._old_urls[
            self._old_urls['cat_title'] == category_row['cat_title']
        ].iterrows():
            if self._match_parsed_product(parsed_item, row):
                print('product already in url store')
                self._add_df_row_from_parsed_product(parsed_item, category_row)
                return
            if self._match_parsed_product_by_url(parsed_item, row):
                parsed_item['title'] = row['title']
                print('product already in url store (but with different name, name in store was updated)')
                self._add_df_row_from_parsed_product(parsed_item, category_row)
                return

        # if we have too few items in current category, add this item
        if len(self._old_urls[self._old_urls['cat_title'] == category_row['cat_title']]) <= 15:
            print('add to url store')
            self._old_urls = self._old_urls.append(
                ignore_index=True,
                other={
                    'cat_title': category_row['cat_title'],
                    'title': parsed_item['title'],
                    'url': parsed_item['url'],
                },
            )
            self._add_df_row_from_parsed_product(parsed_item, category_row)

    def _update_url_list_from_search(self):
        """
        One of main functions. Update item (= product) list with usage of shop search.
        Also, if it can, update price from old item if them equal to searched ones.

        :return: None
        """
        for _, category_row in self._full_category_table.iterrows():

            try:
                parsed_list = self._get_parsed_product_from_search(category_row)
                if parsed_list is None:
                    continue

                if DEVELOP_MODE:
                    print(f'from search parsed {len(parsed_list)} items')

                if len(parsed_list) == 0:
                    # fixme - log - fatal - probably markup of site has changed
                    print(f"zero size of {self.get_handler_name()} on {category_row['cat_title']}, "
                          f"probably markup of site has changed")
                    continue
            except:
                # FIXME fatal log
                print(f'Error while handling search result for:\n'
                      f'handler : {self.get_handler_name()};\n'
                      f'category : {category_row["cat_title"]}')
                continue

            for item in parsed_list:
                postprocess_parsed_product(item, category_row)
                validate_ParsedProduct(item)

                try:
                    if isinstance(category_row['keywords_cons'], str) and len(category_row['keywords_cons']) > 0:
                        if re.search(category_row['keywords_cons'], item['title']) is not None:
                            if DEVELOP_MODE:
                                print(f'del item due to keywords_cons {item["title"]}')
                            continue
                    if isinstance(category_row['keywords_pro'], str) and len(category_row['keywords_pro']) > 0:
                        if re.search(category_row['keywords_pro'], item['title']) is None:
                            if DEVELOP_MODE:
                                print(f'del item due to  keywords_pro {item["title"]}')
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

                if Interface_TEST_MODE:
                    if len(self._old_urls) > 1:
                        print(f'TEST MODE exit search due to find at least one element for handler '
                              f'{self.get_handler_name()}')
                        break
            if Interface_TEST_MODE:
                if len(self._old_urls) > 1:
                    break

        self._old_urls.to_csv(self._get_path_to_old_urls(), index=False)

        if Interface_TEST_MODE:
            self._url_done = set()

    def _get_df_from_url_list(self) -> None:
        """
        One of the main functions. Update items (= products) using urls from stored list.
        """
        for index, url_row in self._old_urls.iterrows():
            # have columns : 'cat_title', 'title', 'url'

            category_row = self._full_category_table[self._full_category_table['cat_title'] == url_row['cat_title']].iloc[0]

            if url_row['title'] in self._url_done:
                # was processed
                continue

            try:
                parsed_product: ParsedProduct = self._get_parsed_product_from_url(url_row['url'])
                if parsed_product is None:
                    continue
                postprocess_parsed_product(parsed_product, category_row)
                validate_ParsedProduct(parsed_product)
            except:
                print(f'in parser {self.get_handler_name()} Error during parsing single item:')
                print(url_row['cat_title'])
                print(url_row['title'])
                print(url_row['url'], end='\n\n')
                continue

            self._add_df_row_from_parsed_product(parsed_product, category_row)

            if Interface_TEST_MODE:
                print(f'TEST MODE exit single due to find at least one element for handler '
                      f'{self.get_handler_name()}')
                break
