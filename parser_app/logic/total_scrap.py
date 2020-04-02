
import pandas as pd
from datetime import datetime
from parser_app.logic.handlers.perekrestok_handler import PerekrestokHandler
from parser_app.logic.handlers.okey_handler import OkeyHandler
from parser_app.logic.handlers.globus_handler import GlobusHandler
from parser_app.logic.handlers.utkonos_handler import UtkonosHandler
import math


class TotalGrocery:

    def get_df(self):
        start = datetime.now()
        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

        site_handlers = [OkeyHandler(), GlobusHandler(), UtkonosHandler(), PerekrestokHandler(), ]  ##

        for handler in site_handlers:
            df = df.append(handler.extract_products())

        date_now = datetime.now().strftime("%Y-%m-%d")
        # df.to_csv(r'D:\ANE_2\parsed_content\grocery_{}.csv'.format(date_now))

        # выявление несобранных категорий
        unq_pivot = df.pivot_table(index='category_id', columns='site_code', values='site_title', aggfunc='nunique')
        df_nan = unq_pivot[unq_pivot.isnull().any(axis=1)]

        bad_df = pd.DataFrame()

        for index, row in df_nan.iterrows():
            for column in row.index:
                if math.isnan(df_nan.loc[index, column]):
                    srs = pd.Series(int(index), name=column)
                    bad_df = bad_df.append(srs)

        bad_df.to_csv(r'D:\ANE_2\parsed_content\bad_grocery_{}.csv'.format(date_now))

        end = datetime.now()
        time_execution = str(end-start)
        print('ALL STORES have successfully parsed\ntotal time of execution: {}'.format(time_execution))

        return df

    def get_df_page(self):
        start = datetime.now()
        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                   'site_title', 'price_new', 'price_old', 'site_unit',
                                   'site_link', 'site_code'])

        site_handlers = [OkeyHandler(), GlobusHandler(), PerekrestokHandler(), UtkonosHandler(), ]  #

        for handler in site_handlers:
            df = df.append(handler.extract_product_page())

        # df.to_csv(r'D:\ANE_2\parsed_content\non-grocery_{}.csv'.format(date_now))
        end = datetime.now()
        time_execution = str(end - start)
        print('ALL GROCERY STORES have successfully parsed\ntotal time of execution: {}'.format(time_execution))
        return df



