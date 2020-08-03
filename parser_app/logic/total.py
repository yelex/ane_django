import sys

from pyvirtualdisplay import Display

from anehome.settings import DEVELOP_MODE
from parser_app.logic.handlers.GKS_handler import GKS_weekly_handler
from parser_app.logic.handlers.NewEldoradoHandler import EldoradoHandlerMSK
from parser_app.logic.handlers.NewLenta_handler import LentaHandlerMSK, LentaHandlerSPB
from parser_app.logic.handlers.NewOkey_handler import OkeyHandlerSPB
from parser_app.logic.handlers.NewPerekrestok_handler import PerekrestokHandlerSPB
from parser_app.logic.handlers.NewRigla_handler import RiglaHandlerSPB
from parser_app.logic.handlers.NewIKEA_handler import IkeaHandlerMSK
from parser_app.logic.handlers.NewSvaznoy_handler import SvaznoyHandlerMSK
from parser_app.logic.handlers.handler_tools import get_empty_handler_DF
from parser_app.logic.total_scrap import TotalGrocery
from parser_app.logic.total_neprod import TotalNongrocery
from parser_app.logic.handlers.services_handler import Services
from parser_app.logic.handlers.tools import perpetualTimer, fill_df, get_basket_df
from parser_app.logic.global_status import Global, create_tor_webdriver
from parser_app.models import PricesRaw, Gks, Basket
import pandas as pd
from datetime import datetime

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # test_ane


class Total:

    def printer_test(self):
        function_start_time = datetime.now()

        Global().getproxies()
        print('Timer call : start making snapshots')

        date_now = datetime.now().strftime("%Y-%m-%d")

        print('Timer call : start making snapshots')

        df = get_empty_handler_DF()

        # use display from pyVirtual display package in order to launch selenium not in a real window
        with Display():
            # tor_webdriver = create_tor_webdriver()
            # df = df.append(IkeaHandlerMSK(tor_driver=tor_webdriver).extract_products())
            # df = df.append(RiglaHandlerSPB(tor_driver=tor_webdriver).extract_products())
            # df = df.append(PerekrestokHandlerSPB(tor_driver=tor_webdriver).extract_products())
            # df = df.append(OkeyHandlerSPB(tor_driver=tor_webdriver).extract_products())
            # tor_webdriver.quit()

            df = df.append(IkeaHandlerMSK(proxy_method='tor-service').extract_products())
            df = df.append(RiglaHandlerSPB(proxy_method='tor-service').extract_products())
            df = df.append(PerekrestokHandlerSPB(proxy_method='tor-service').extract_products())
            df = df.append(OkeyHandlerSPB(proxy_method='tor-service', use_request=True).extract_products())

            df = df.append(SvaznoyHandlerMSK(proxy_method='no-proxy').extract_products())
            df = df.append(EldoradoHandlerMSK(proxy_method='tor-service').extract_products())

            df = df.append(LentaHandlerMSK(proxy_method='no-proxy').extract_products())
            df = df.append(LentaHandlerSPB(proxy_method='no-proxy').extract_products())

        with Display():
            try:
                df = df.append(TotalGrocery().get_df_page())
            except:
                print('ERROR while handling TotalGrocery')

            try:
                df = df.append(TotalNongrocery().get_df_page())
            except:
                print('ERROR while handling TotalNongrocery')

            try:
                df = df.append(Services().get_df())
            except:
                print('ERROR while handling Services')

        # uncomment for tests
        # df = pd.read_csv(os.path.join('parser_app', 'logic', 'description', 'df_after_handlers_FOR_TESTS.csv'))

        df['date'] = date_now

        df = df.sort_values(['category_id', 'site_link'])

        df['miss'] = 0
        df.reset_index(drop=True, inplace=True)

        path_to_parsed_content_folder = 'parsed_content'
        if not os.path.exists(path_to_parsed_content_folder):
            os.makedirs(path_to_parsed_content_folder)

        df_path = os.path.join('parsed_content', 'data_test_{}.csv'.format(date_now))
        pivot_path = os.path.join('parsed_content', 'pivot_test_{}.csv'.format(date_now))

        pivot = df.pivot_table(
            index='category_id',
            columns=['type', 'site_code'],
            values='site_link',
            aggfunc='nunique'
        )

        if sys.platform.startswith('linux'):
            df.to_csv(df_path)
            pivot.to_csv(pivot_path)
        elif sys.platform.contain('win'):
            df.to_csv(os.path.join(r'D:\ANE_2', df_path))
            pivot.to_csv(os.path.join(r'D:\ANE_2', pivot_path))
        else:
            raise ValueError("your operation system not found")

        df['price_old'] = df['price_old'].replace('', -1.0)
        df['price_old'] = df['price_old'].fillna(-1.0)

        cached_list = []
        print('Storing raw prices to db...')
        for _, row in df.iterrows():
            prod = PricesRaw(
                date=row['date'],
                type=row['type'],
                category_id=row['category_id'],
                category_title=row['category_title'],
                site_title=row['site_title'],
                price_new=row['price_new'],
                price_old=row['price_old'],
                site_unit=row['site_unit'],
                site_link=row['site_link'],
                site_code=row['site_code'],
                miss=row['miss'],
            )
            cached_list.append(prod)
        PricesRaw.objects.bulk_create(cached_list)
        print('Storing complete!')

        print('Filling df...')
        filled_df = fill_df(pd.DataFrame(list(PricesRaw.objects.all().values())))
        filled_df.to_csv(os.path.join('parsed_content', 'filled_df.csv'))
        print('Filling complete!')

        df_gks = GKS_weekly_handler().get_df()
        cached_list = []

        Gks.objects.all().delete()
        print('Storing gks prices to db...')
        for _, row in df_gks.iterrows():
            prod = Gks(
                date=row['date'],
                type=row['type'],
                category_id=row['category_id'],
                category_title=row['category_title'],
                site_title=row['site_title'],
                price_new=row['price_new'],
                price_old=row['price_old'],
                site_unit=row['site_unit'],
                site_link=row['site_link'],
                site_code=row['site_code'],
                miss=row['miss'],
            )
            cached_list.append(prod)
        Gks.objects.bulk_create(cached_list)
        print('Storing complete!')

        print('Getting basket df...')
        basket_df = get_basket_df(
            df_gks[df_gks['type'] == 'food'],
            filled_df[filled_df['type'] == 'food'],
        )
        print('Getting complete!')

        print('Storing basket to db...')
        cached_list = []
        Basket.objects.all().delete()
        for _, row in basket_df.iterrows():
            prod = Basket(
                date=row['date'],
                gks_price=row['gks_price'],
                online_price=row['online_price'],
            )
            cached_list.append(prod)
        Basket.objects.bulk_create(cached_list)
        print('Storing completed!')

        function_end_time = datetime.now()
        time_execution = str(function_end_time - function_start_time)

        print('PARSING ENDED!\ntotal time of all execution: {}'.format(time_execution))

    def get_new_snap_threaded(self):
        tim = perpetualTimer(24 * 60 * 60, self.printer_test)
        tim.start()
