
import pandas as pd
from datetime import datetime
from parser_app.logic.handlers.ozon_handler import OzonHandler
from parser_app.logic.handlers.lamoda_handler import LamodaHandler
from parser_app.logic.handlers.piluli_handler import PiluliHandler
from parser_app.logic.handlers.mvideo_handler import MvideoHandler


class TotalNongrocery():

    def get_df(self):
        start = datetime.now()
        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

        site_handlers = [LamodaHandler(), OzonHandler(),
                         MvideoHandler(), PiluliHandler()]  #

        # max_n = 200

        for handler in site_handlers:
            df = df.append(handler.extract_products())

        # df.to_csv(r'D:\ANE_2\parsed_content\non-grocery_{}.csv'.format(date_now))
        end = datetime.now()
        time_execution = str(end-start)
        print('ALL NON-GROCERY STORES have successfully parsed\ntotal time of execution: {}'.format(time_execution))
        return df

    def get_df_page(self):
        start = datetime.now()
        df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                   'site_title', 'price_new', 'price_old', 'site_unit',
                                   'site_link', 'site_code'])


        site_handlers = [OzonHandler(), LamodaHandler(), ]  # MvideoHandler(),

        for handler in site_handlers:

            df = df.append(handler.extract_product_page())

        df = df.append(PiluliHandler().extract_products())
        # df.to_csv(r'D:\ANE_2\parsed_content\non-grocery_{}.csv'.format(date_now))
        end = datetime.now()
        time_execution = str(end-start)
        print('ALL NON-GROCERY STORES have successfully parsed\ntotal time of execution: {}'.format(time_execution))
        return df

