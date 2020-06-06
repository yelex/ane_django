import sys

from pyvirtualdisplay import Display

from anehome.settings import DEVELOP_MODE
from parser_app.logic.handlers.NewEldoradoHandler import EldoradoHandlerMSK
from parser_app.logic.handlers.NewLenta_handler import LentaHandlerMSK, LentaHandlerSPB
from parser_app.logic.handlers.NewOkey_handler import OkeyHandlerSPB
from parser_app.logic.handlers.NewPerekrestok_handler import PerekrestokHandlerSPB
from parser_app.logic.handlers.NewRigla_handler import RiglaHandlerSPB
from parser_app.logic.handlers.NewIKEA_handler import IkeaHandlerMSK
from parser_app.logic.handlers.NewSvaznoy_handler import SvaznoyHandlerMSK
from parser_app.logic.total_scrap import TotalGrocery
from parser_app.logic.total_neprod import TotalNongrocery
from parser_app.logic.handlers.services_handler import Services
from parser_app.logic.handlers.tools import perpetualTimer, fill_df, get_basket_df
from parser_app.logic.global_status import Global
from parser_app.logic.handlers.gks_handler import SiteHandlerGks
from parser_app.models import PricesRaw, PricesProcessed, Gks, Basket
import pandas as pd
from datetime import datetime

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # test_ane


class Total:

    def printer_test(self):

        Global().getproxies()
        print('Timer call : start making snapshots')
        start = datetime.now()
        date_now = datetime.now().strftime("%Y-%m-%d")

        print('Timer call : start making snapshots')

        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                   'site_title', 'price_new', 'price_old', 'site_unit',
                                   'site_link', 'site_code'])

        # use display from pyVirtual display package in order to launch selenium not in a real window
        with Display():
            df = df.append(SvaznoyHandlerMSK().extract_products())
            df = df.append(IkeaHandlerMSK().extract_products())
            df = df.append(RiglaHandlerSPB().extract_products())
            df = df.append(EldoradoHandlerMSK().extract_products())
            df = df.append(PerekrestokHandlerSPB().extract_products())
            df = df.append(LentaHandlerMSK().extract_products())
            df = df.append(LentaHandlerSPB().extract_products())
            df = df.append(OkeyHandlerSPB().extract_products())

            df = df.append(TotalGrocery().get_df_page())
            df = df.append(TotalNongrocery().get_df_page())
            df = df.append(Services().get_df())

        # uncomment for tests
        # df = pd.read_csv(os.path.join('parser_app', 'logic', 'description', 'df_after_handlers_FOR_TESTS.csv'))

        df['date'] = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

        # df = df.drop_duplicates(subset=['date', 'category_id', 'site_link'])
        df = df.sort_values(['category_id', 'site_link'])

        # conn = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))
        df['miss'] = 0
        df.reset_index(drop=True, inplace=True)

        path_to_parsed_content_folder = 'parsed_content'
        if not os.path.exists(path_to_parsed_content_folder):
            os.makedirs(path_to_parsed_content_folder)
        df_path = os.path.join(path_to_parsed_content_folder, 'data_test_{}.csv'.format(date_now))
        pivot_path = os.path.join(path_to_parsed_content_folder, 'pivot_test_{}.csv'.format(date_now))


        # df.to_csv(os.path.join(Global().path_parsedcontent, 'data_test_{}.csv').format(date_now))
        # pivot = df.pivot_table(index='category_id', columns=['type', 'site_code'],
        #                        values='site_link', aggfunc='nunique')
        # pivot.to_csv(os.path.join(Global().path_parsedcontent, 'pivot_test_{}.csv').format(date_now))

        df_path = os.path.join('parsed_content', 'data_test_{}.csv'.format(date_now))
        pivot_path = os.path.join('parsed_content', 'pivot_test_{}.csv'.format(date_now))

        pivot = df.pivot_table(index='category_id', columns=['type', 'site_code'],values='site_link', aggfunc='nunique')

        if sys.platform.startswith('linux'):
            df.to_csv(df_path)
            pivot.to_csv(pivot_path)
        elif sys.platform.contain('win'):
            df.to_csv(os.path.join(r'D:\ANE_2', df_path))
            pivot.to_csv(os.path.join(r'D:\ANE_2', pivot_path))
        else:
            raise ValueError("your operation system not found")

        df.loc[:, 'price_old'] = df.loc[:, 'price_old'].replace('', -1.0)
        df.loc[:, 'price_old'] = df.loc[:, 'price_old'].fillna(-1.0)

        cached_list = []
        print('Storing raw prices to db...')
        for _, row in df.iterrows():
            # product = ProductHandler(**dict(row))
            # cached_list.append(product)
            # Person.objects.bulk_create(person_list)
            prod = PricesRaw(date=row['date'],
                             type=row['type'],
                             category_id=row['category_id'],
                             category_title=row['category_title'],
                             site_title=row['site_title'],
                             price_new=row['price_new'],
                             price_old=row['price_old'],
                             site_unit=row['site_unit'],
                             site_link=row['site_link'],
                             site_code=row['site_code'],
                             miss=row['miss'])
            cached_list.append(prod)

            # m.save()
        PricesRaw.objects.bulk_create(cached_list)
        print('Storing complete!')


        print('Storing gks prices to db...')

        print('Filling df...')
        filled_df = fill_df(pd.DataFrame(list(PricesRaw.objects.all().values())))
        if sys.platform.startswith('linux'):
            filled_df.to_csv(os.path.join('parsed_content', 'filled_df.csv'))
        elif sys.platform.contain('win'):
            filled_df.to_csv(r'D:\ANE_2\parsed_content\filled_df.csv')
        else:
            raise ValueError("your operation system not found")
        print('Filling complete!')

        df_gks = SiteHandlerGks().get_df()
        cached_list = []

        Gks.objects.all().delete()
        print('Storing gks prices to db...')
        for _, row in df_gks.iterrows():
            prod = Gks(date=row['date'],
                       type=row['type'],
                       category_id=row['category_id'],
                       category_title=row['category_title'],
                       site_title=row['site_title'],
                       price_new=row['price_new'],
                       price_old=row['price_old'],
                       site_unit=row['site_unit'],
                       site_link=row['site_link'],
                       site_code=row['site_code'],
                       miss=row['miss'])
            cached_list.append(prod)

            # m.save()

        Gks.objects.all().delete()
        Gks.objects.bulk_create(cached_list)
        print('Storing complete!')

        print('Getting basket df...')
        basket_df = get_basket_df(df_gks, filled_df.loc[filled_df.type == 'food', :])
        print('Getting complete!')

        # basket_df.to_csv('basket_df.csv')
        # basket_df.to_csv(r'D:\ANE_2\parsed_content\basket_df.csv')

        print('Storing basket to db...')

        # try:
        cached_list = []
        Basket.objects.all().delete()
        for _, row in basket_df.iterrows():
            prod = Basket(
                date=row['date'],
                gks_price=row['gks_price'],
                online_price=row['online_price'],
            )
            cached_list.append(prod)
            # m.save()
        Basket.objects.bulk_create(cached_list)
        print('Storing completed!')
        # except:
        #     print('fail to create backet sql base')

        end = datetime.now()
        time_execution = str(end - start)
        # send_mail(message='Снапшот успешно создан {}'.format(end))

        print('PARSING ENDED!\ntotal time of all execution: {}'.format(time_execution))

        if Global().is_shutdown is True and not DEVELOP_MODE:
            # os.system('shutdown /p /f') # windows
            os.system('systemctl poweroff') # linux

    def get_new_snap_threaded(self):
        tim = perpetualTimer(24 * 60 * 60, self.printer_test)
        tim.start()


"""


def printer():
    start = datetime.now()
    date_now = datetime.now().strftime("%Y-%m-%d")
    print('Timer call : start making snapshots')
    df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                               'site_title', 'price_new', 'price_old', 'site_unit',
                               'site_link', 'site_code'])

    df = df.append(TotalNongrocery().get_df())
    df = df.append(Services().get_df())
    df = df.append(TotalGrocery().get_df())



    df = df.drop_duplicates(subset=['date', 'category_id', 'site_link'])
    df = df.sort_values(['category_id', 'site_link'])


    conn = sqlite3.connect(r'D:\test_ane\db19.sqlite')
    # c = conn.cursor()

    # db = pd.read_sql(sql='select * from prices', con=conn)
    # print('df.columns', df.columns)
    # print('db.columns', db.columns)
    # dropTableStatement = "DROP TABLE IF EXISTS prices"

    # c.execute(dropTableStatement)

    # db = db.drop_duplicates(subset=['date', 'category_id', 'site_link'])
    df.to_csv(r'D:\ANE_2\parsed_content\data_{}.csv'.format(date_now))
    # db.to_sql(name='prices', con=conn, if_exists='append', index=False)
    df.to_sql(name='prices', con=conn, if_exists='append', index=False)
    end = datetime.now()
    time_execution = str(end - start)
    print('PARSING ENDED!\ntotal time of execution: {}'.format(time_execution))

tim = perpetualTimer(86400, printer)
tim.start()
"""
