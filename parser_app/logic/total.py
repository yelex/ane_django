
from parser_app.logic.total_scrap import TotalGrocery
from parser_app.logic.total_neprod import TotalNongrocery
from parser_app.logic.handlers.services_handler import Services
from parser_app.logic.handlers.tools import perpetualTimer, fill_df, get_basket_df
from parser_app.logic.global_status import Global
from parser_app.logic.handlers.gks_handler import SiteHandlerGks
import pandas as pd
from datetime import datetime
import sqlite3

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # test_ane

class Total:

    def printer_test(self):

        print('Timer call : start making snapshots')
        start = datetime.now()
        date_now = Global().date

        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                   'site_title', 'price_new', 'price_old', 'site_unit',
                                   'site_link', 'site_code'])


        df = df.append(TotalNongrocery().get_df_page())
        df = df.append(TotalGrocery().get_df_page())
        df = df.append(Services().get_df())
        df.loc[:, 'date'] = pd.to_datetime(df.loc[:, 'date'])

        # df = df.drop_duplicates(subset=['date', 'category_id', 'site_link'])
        df = df.sort_values(['category_id', 'site_link'])

        conn = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))
        df.reset_index(drop=True, inplace=True)
        df.loc[:, 'miss'] = 0

        df.to_csv(r'D:\ANE_2\parsed_content\data_test_{}.csv'.format(date_now))
        pivot = df.pivot_table(index='category_id', columns=['type', 'site_code'],
                               values='site_link', aggfunc='nunique')
        pivot.to_csv(r'D:\ANE_2\parsed_content\pivot_test_{}.csv'.format(date_now))
        df.loc[:, 'price_old'] = df.loc[:, 'price_old'].fillna(-1.0)
        df.to_sql(name='parser_app_pricesraw', con=conn, if_exists='append', index=False)
        filled_df = fill_df(pd.read_sql(sql='SELECT * FROM parser_app_pricesraw', con=conn))
        filled_df.to_sql(name='parser_app_pricesprocessed', con=conn, if_exists='replace', index=False)
        df_gks = SiteHandlerGks().get_df()
        df_gks.to_sql(name='parser_app_gks', con=conn, if_exists='replace', index=False)
        basket_df = get_basket_df(df_gks, filled_df[filled_df.type == 'food'])
        basket_df.to_sql(name='parser_app_basket', con=conn, if_exists='replace', index=True)
        end = datetime.now()
        time_execution = str(end - start)
        # send_mail(message='Снапшот успешно создан {}'.format(end))

        print('PARSING ENDED!\ntotal time of execution: {}'.format(time_execution))



    def get_new_snap_threaded(self):
        print('Start making snapshot!')
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

