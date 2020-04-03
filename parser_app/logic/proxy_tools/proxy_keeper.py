import os

import pandas as pd
import numpy as np
from typing import List
from selenium import webdriver

from parser_app.logic.global_status import create_webdriver_with_proxy
from parser_app.logic.proxy_tools.common_proxy_testers import simple_test_is_proxy_suit

from parser_app.logic.proxy_tools.proxy_habdler_interface import ProxyHandlerInterface
from parser_app.logic.proxy_tools.proxy_handler_PROXYNOVA import ProxynovaProxyHandler
from parser_app.logic.proxy_tools.proxy_habdler_HIDEMY import HidemyProxyHandler


USED_PROXY_HANDLERS: List[ProxyHandlerInterface] = [HidemyProxyHandler(), ]  # ProxynovaProxyHandler()]


class ProxyKeeper:

    def __init__(self):
        # list of proxy; columns : proxy (str),
        self._proxy_list: pd.DataFrame

        # pd.DF of pairs: proxy(str), handler_name(str);
        #   if pair in df, pair's proxy shouldn't be used for handler
        self._not_suit_proxy: pd.DataFrame

        self._reload_from_disk()

    def get_proxy_for_site(self, site_handler) -> webdriver.Chrome:
        """
        site_handler MUST ME HandlerInterface instance
        """
        # actually unusual case
        if len(self._proxy_list) == 0:
            self.update_proxy_list(3128)

        while True:
            all_possible_ips: List[str] = list(self._proxy_list['proxy'].values)
            excluded_ip: List[str] = list(
                self._not_suit_proxy[self._not_suit_proxy['handler'] == site_handler.get_handler_name()]['proxy']
            )
            choose_from = list(set(all_possible_ips) - set(excluded_ip))
            if len(choose_from) == 0:
                raise ValueError(f'no proxy suit handler : {site_handler.get_handler_name()}')

            ip_to_test: str = np.random.choice(choose_from)
            driver = create_webdriver_with_proxy(ip_to_test)

            if not simple_test_is_proxy_suit(ip_to_test, site_handler):
                # FIXME event log
                print(f"proxy did not pass simple tests : {ip_to_test}")
                self._mark_proxy_not_suit_handler(ip_to_test, site_handler.get_handler_name())
                continue

            if not site_handler.test_web_driver(driver):
                # FIXME event log
                print(f"proxy did not pass handler ({site_handler.get_handler_name}) tests : {ip_to_test}")
                self._mark_proxy_not_suit_handler(ip_to_test, site_handler.get_handler_name())
                continue

            # FIXME success log
            print(f"proxy  *{ip_to_test}* suit handler : {site_handler.get_handler_name()}")
            break

        self.remove_not_suited_proxy()

        return driver

    def _mark_proxy_not_suit_handler(self, proxy: str, handler_name: str) -> None:
        self._not_suit_proxy = self._not_suit_proxy.append(
            {'proxy': proxy, 'handler': handler_name},
            ignore_index=True,
        )
        self._save_to_disk()

    def remove_not_suited_proxy(self) -> None:
        """
        remove proxy ip from global list if this ip not suit for
        at least 'NUMBER_NOT_SUITED_SITE_TO_DEL' site handlers
        :return: nothing
        """
        NUMBER_NOT_SUITED_SITE_TO_DEL = 2

        proxy_to_del = []
        for _, row in self._proxy_list.iterrows():
            proxy = row['proxy']

            if len(self._not_suit_proxy[self._not_suit_proxy['proxy'] == proxy]) > NUMBER_NOT_SUITED_SITE_TO_DEL:
                proxy_to_del.append(row.index)

        self._proxy_list.drop(proxy_to_del, inplace=True)

    def update_proxy_list(self, port: int = 3128) -> None:
        add_ip_stats = {'proxy_fails': 0, 'new_ip_added': 0, 'handlers_fails': []}
        ip_list: List[str] = []
        for proxy_handler in USED_PROXY_HANDLERS:
            try:
                ip_list.extend(proxy_handler.get_proxy_list(port))
            except:
                add_ip_stats['proxy_fails'] += 1
                add_ip_stats['handlers_fails'].append(proxy_handler.get_name())
                print(f'Error while proceccing proxy handler {proxy_handler.get_name()}')

        for ip_item in ip_list:
            if ip_item in self._proxy_list['proxy'].values:
                continue
            self._proxy_list = self._proxy_list.append({'proxy': ip_item}, ignore_index=True)
            add_ip_stats['new_ip_added'] += 1

        print(f'proxy update stats\n: {add_ip_stats}')

        self.remove_not_suited_proxy()
        self._save_to_disk()

    @staticmethod
    def get_path_to_proxy_list() -> str:
        return os.path.join('.', 'parser_app', 'logic', 'proxy_tools', 'proxy_list.csv')

    @staticmethod
    def get_path_to_not_suited_list() -> str:
        return os.path.join('.', 'parser_app', 'logic', 'proxy_tools', 'not_suit_list.csv')


    @staticmethod
    def _create_file_if_not_exist() -> None:
        # make sure that folder exist
        if not os.path.exists(os.path.dirname(ProxyKeeper.get_path_to_proxy_list())):
            os.makedirs(os.path.dirname(ProxyKeeper.get_path_to_proxy_list()))

        # load proxy list
        if not os.path.exists(ProxyKeeper.get_path_to_proxy_list()):
            df = pd.DataFrame(columns=['proxy'])
            df.to_csv(ProxyKeeper.get_path_to_proxy_list(), index=False)

        # load not suited proxy pairs
        if not os.path.exists(ProxyKeeper.get_path_to_not_suited_list()):
            df = pd.DataFrame(columns=['proxy', 'handler'])
            df.to_csv(ProxyKeeper.get_path_to_not_suited_list(), index=False)


    def _reload_from_disk(self) -> None:
        ProxyKeeper._create_file_if_not_exist()
        self._proxy_list = pd.read_csv(ProxyKeeper.get_path_to_proxy_list())
        self._not_suit_proxy = pd.read_csv(ProxyKeeper.get_path_to_not_suited_list())

    def _save_to_disk(self) -> None:
        ProxyKeeper._create_file_if_not_exist()
        self._proxy_list.to_csv(ProxyKeeper.get_path_to_proxy_list(), index=False)
        self._not_suit_proxy.to_csv(ProxyKeeper.get_path_to_not_suited_list(), index=False)

