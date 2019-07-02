
from .total_scrap import TotalGrocery
from .total_neprod import TotalNongrocery
from .handlers.services_handler import Services
from .handlers.tools import perpetualTimer, send_mail
from parser_app.models import PricesRaw
import pandas as pd
from parser_app.logic.handlers.global_status import Global
from datetime import datetime
import sqlite3

#df = LamodaHandler().extract_product_page()
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # test_ane


class Total():

    def printer_test(self):

        print('Timer call : start making snapshots')
        start = datetime.now()
        date_now = datetime.now().strftime("%Y-%m-%d")

        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                   'site_title', 'price_new', 'price_old', 'site_unit',
                                   'site_link', 'site_code'])

        df = df.append(TotalNongrocery().get_df_page())
        df = df.append(Services().get_df())
        df = df.append(TotalGrocery().get_df_page())


        df = df.drop_duplicates(subset=['date', 'category_id', 'site_link'])
        df = df.sort_values(['category_id', 'site_link'])

        df.to_csv(r'D:\ANE_2\parsed_content\data_test_{}.csv'.format(date_now))
        pivot = df.pivot_table(index='category_id', columns=['type', 'site_code'],
                               values='site_link', aggfunc='nunique')
        pivot.to_csv(r'D:\ANE_2\parsed_content\pivot_test_{}.csv'.format(date_now))
        # db.to_sql(name='prices', con=conn, if_exists='append', index=False)
        store_to_db(df)
        end = datetime.now()
        time_execution = str(end - start)
        # send_mail(message='Снапшот успешно создан {}'.format(end))
        
        print('PARSING ENDED!\ntotal time of execution: {}'.format(time_execution))

    def get_new_snap_threaded(self):
        tim = perpetualTimer(86400, self.printer_test)
        tim.start()


def store_to_db(df):
    print('Storing to db...')
    site_codes = df.site_code.unique()
    df['miss'] = 0
    df['price_old'] = df['price_old'].replace('', -1.0)
    for site_code in site_codes:
        df = df[df.site_code == site_code]
        cached_list = []
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

