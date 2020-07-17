import json
import os
import pickle
import time
from datetime import datetime

import pandas as pd
import numpy as np
from typing import List
from selenium import webdriver

from anehome.settings import DEVELOP_MODE
from parser_app.logic.global_status import create_webdriver_with_proxy, create_webdriver
# from parser_app.logic.proxy_tools.common_proxy_testers import simple_test_is_proxy_suit
from parser_app.logic.proxy_tools.common_proxy_testers import simple_test_driver_with_url

from parser_app.logic.proxy_tools.proxy_habdler_interface import ProxyHandlerInterface
from parser_app.logic.proxy_tools.proxy_handler_PROXYNOVA import ProxynovaProxyHandler
from parser_app.logic.proxy_tools.proxy_habdler_HIDEMY import HidemyProxyHandler


# UNCOMMENT ProxynovaProxyHandler TO GET MORE PROXIES,
# but these proxy not so stable as HidemyProxyHandler and may work slowly
USED_PROXY_HANDLERS: List[ProxyHandlerInterface] = [
    HidemyProxyHandler(),
#    ProxynovaProxyHandler(),
]


FULL_UPDATE_EVERY_HOUR: bool = DEVELOP_MODE


class ProxyKeeper:

    def __init__(self):
        # list of proxy; columns : proxy (str),
        self._proxy_list: pd.DataFrame

        # pd.DF of pairs: proxy(str), handler_name(str);
        #   if pair in df, pair's proxy shouldn't be used for handler
        self._not_suit_proxy: pd.DataFrame

        self._reload_from_disk()
        ProxyKeeper._create_file_if_not_exist()
        last_update_date = json.load(open(os.path.join(ProxyKeeper.get_base_dir_path(), 'last_update.json'), 'r'))['last_update']
        print(f'last update date : {last_update_date}, current time : {ProxyKeeper._get_time_in_hours()}')

        if last_update_date != ProxyKeeper._get_time_in_hours():
            if FULL_UPDATE_EVERY_HOUR:
                os.remove(self.get_path_to_proxy_list())
                os.remove(self.get_path_to_not_suited_list())
            self.update_proxy_list()

    def get_web_driver_for_site(self, site_handler, **driver_options) -> webdriver.Chrome:
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

            # to test proxy set it here
            # ip_to_test = "51.178.220.168:3128"

            driver = create_webdriver(proxy_ip_with_port=ip_to_test, **driver_options)

            if not simple_test_driver_with_url(driver, site_handler.get_test_url()):
                # FIXME event log
                print(f"proxy did not pass simple tests : {ip_to_test}")
                self._mark_proxy_not_suit_handler(ip_to_test, site_handler.get_handler_name())
                try:
                    driver.quit()
                except:
                    pass
                continue

            if not site_handler.test_web_driver(driver):
                # FIXME event log
                print(f"proxy did not pass handler ({site_handler.get_handler_name}) tests : {ip_to_test}")
                self._mark_proxy_not_suit_handler(ip_to_test, site_handler.get_handler_name())
                try:
                    driver.quit()
                except:
                    pass
                continue

            # FIXME success log
            print(f"proxy  *{ip_to_test}* suit handler : {site_handler.get_handler_name()}")
            break

        # self.remove_not_suited_proxy()

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
        # FIXME routine log
        print('start to update proxy list')

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

        try:
            # self.remove_not_suited_proxy()
            self._save_to_disk()
            json.dump(
                {'last_update': ProxyKeeper._get_time_in_hours()},
                open(os.path.join(ProxyKeeper.get_base_dir_path(), 'last_update.json'), 'w'),
            )
        except:
            # FIXME log fatal
            print("error in saving proxy after update")
            print("probably, nothing was saved")

        print(f'proxy update stats\n: {add_ip_stats}')

    @staticmethod
    def get_base_dir_path() -> str:
        return os.path.join('.', 'parser_app', 'logic', 'proxy_tools', 'store')

    @staticmethod
    def get_path_to_proxy_list() -> str:
        return os.path.join(ProxyKeeper.get_base_dir_path(), 'proxy_list.csv')

    @staticmethod
    def get_path_to_not_suited_list() -> str:
        return os.path.join(ProxyKeeper.get_base_dir_path(), 'not_suit_list.csv')


    @staticmethod
    def _create_file_if_not_exist() -> None:
        # make sure that folder exist
        if not os.path.exists(ProxyKeeper.get_base_dir_path()):
            os.makedirs(os.path.dirname(ProxyKeeper.get_path_to_proxy_list()))

        # load proxy list
        if not os.path.exists(ProxyKeeper.get_path_to_proxy_list()):
            df = pd.DataFrame(columns=['proxy'])
            df.to_csv(ProxyKeeper.get_path_to_proxy_list(), index=False)

        # load not suited proxy pairs
        if not os.path.exists(ProxyKeeper.get_path_to_not_suited_list()):
            df = pd.DataFrame(columns=['proxy', 'handler'])
            df.to_csv(ProxyKeeper.get_path_to_not_suited_list(), index=False)

        if not os.path.exists(os.path.join(ProxyKeeper.get_base_dir_path(), 'last_update.json')):
            json.dump(
                {'last_update': ProxyKeeper._get_time_in_hours() - 1000},
                open(os.path.join(ProxyKeeper.get_base_dir_path(), 'last_update.json'), 'w+'),
            )

    @staticmethod
    def _get_time_in_hours() -> int:
        return int(int(round(time.time())) / 60 / 60)

    def _reload_from_disk(self) -> None:
        ProxyKeeper._create_file_if_not_exist()
        self._proxy_list = pd.read_csv(ProxyKeeper.get_path_to_proxy_list())
        self._not_suit_proxy = pd.read_csv(ProxyKeeper.get_path_to_not_suited_list())

    def _save_to_disk(self) -> None:
        ProxyKeeper._create_file_if_not_exist()
        self._proxy_list.to_csv(ProxyKeeper.get_path_to_proxy_list(), index=False)
        self._not_suit_proxy.to_csv(ProxyKeeper.get_path_to_not_suited_list(), index=False)

