
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

        # Global().getproxies()
        print('Timer call : start making snapshots')
        start = datetime.now()

        # df_gks = SiteHandlerGks().get_df()
        # cached_list = []
        #
        # print('Storing gks prices to db...')
        #
        # for _, row in df_gks.iterrows():
        #     prod = Gks(date=row['date'],
        #                type=row['type'],
        #                category_id=row['category_id'],
        #                category_title=row['category_title'],
        #                site_title=row['site_title'],
        #                price_new=row['price_new'],
        #                price_old=row['price_old'],
        #                site_unit=row['site_unit'],
        #                site_link=row['site_link'],
        #                site_code=row['site_code'],
        #                miss=row['miss'])
        #     cached_list.append(prod)
        #
        #     # m.save()
        # Gks.objects.all().delete()
        # Gks.objects.bulk_create(cached_list)
        # print('Storing complete!')

        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                   'site_title', 'price_new', 'price_old', 'site_unit',
                                   'site_link', 'site_code'])

        df = df.append(TotalGrocery().get_df_page())
        df = df.append(TotalNongrocery().get_df_page())
        df = df.append(Services().get_df())

        df.loc[:, 'date'] = pd.to_datetime(df.loc[:, 'date'])

        # df = df.drop_duplicates(subset=['date', 'category_id', 'site_link'])
        df = df.sort_values(['category_id', 'site_link'])

        # conn = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))
        df.reset_index(drop=True, inplace=True)
        df.loc[:, 'miss'] = 0

        # df.to_csv(os.path.join(Global().path_parsedcontent, 'data_test_{}.csv').format(date_now))
        # pivot = df.pivot_table(index='category_id', columns=['type', 'site_code'],
        #                        values='site_link', aggfunc='nunique')
        # pivot.to_csv(os.path.join(Global().path_parsedcontent, 'pivot_test_{}.csv').format(date_now))
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

        print('Filling df...')
        filled_df = fill_df(pd.DataFrame(list(PricesRaw.objects.all().values())))
        filled_df.to_csv(os.path.join(Global().path_parsedcontent, 'filled.csv'))
        print('Filling complete!')


        # print('Getting basket df...')
        # basket_df = get_basket_df(df_gks, filled_df.loc[filled_df.category_id.isin(range(1, 34)), :])
        # print('Getting complete!')
        #
        # # basket_df.to_csv('basket_df.csv')
        # # basket_df.to_csv(r'D:\ANE_2\parsed_content\basket_df.csv')
        # cached_list = []
        #
        # print('Storing basket to db...')
        # Basket.objects.all().delete()
        #
        # for _, row in basket_df.iterrows():
        #
        #     prod = Basket(date=row['date'],
        #                gks_price=row['gks_price'],
        #                online_price=row['online_price'])
        #     cached_list.append(prod)
        #     # m.save()
        # Basket.objects.bulk_create(cached_list)
        # print('Storing completed!')
        end = datetime.now()
        time_execution = str(end - start)
        # send_mail(message='Снапшот успешно создан {}'.format(end))

        print('PARSING ENDED!\ntotal time of all execution: {}'.format(time_execution))

        if Global().is_shutdown is True:
        #    os.system('shutdown /p /f') # windows
            os.system('systemctl poweroff') # linux

    def get_new_snap_threaded(self):
        tim = perpetualTimer(86400, self.printer_test)
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

