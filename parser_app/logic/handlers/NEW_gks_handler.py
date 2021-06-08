import requests
import pandas as pd
from datetime import datetime
from typing import List
from sqlalchemy import create_engine


class SiteHandlerGks:
    def __init__(self, last_parsing_date):  # last_parsing_date from Global
        self.path_final_links = r'~/PycharmProjects/ane_django/parser_app/logic/description/final_links.csv'
        self.engine = create_engine(r'mysql+pymysql://root:Fokina12@localhost/ane_base')
        self.date_end_gks = self._get_last_avaliable_date_gks()
        self.date_end_local = self._get_last_avaliable_date_local()
        self.is_parsing_needed = self._is_parsing_needed(self.date_end_gks, self.date_end_local)
        self.gks_links_to_categoryids = self._get_gks_links_to_categoryids()
        self._last_parsing_date = last_parsing_date

    def _is_parsing_needed(self, date_end_gks, date_end_local):
        date_end_gks = self._get_last_avaliable_date_gks()
        date_end_local = self._get_last_avaliable_date_local()
        return date_end_gks > date_end_local

    def _get_last_avaliable_date_gks(self):
        '''
        Return last avaliable date from GKS server for month prices in format 'YYYY-MM-DD'
        '''
        r = requests.get(url='https://showdata.gks.ru/backbone/used-elements/?chain=-64&sources=277328&_=1622907888108')
        last_avaliable_date = r.json()['used_elements'][-1][:10]
        return last_avaliable_date

    def _get_last_avaliable_date_local(self):  # TODO
        sql_str = 'SELECT date FROM parser_app_pricesraw WHERE site_code="gks" ORDER BY date DESC LIMIT 1'
        last_local_date_sql = pd.read_sql(sql=sql_str, con=self.engine)
        if last_local_date_sql.values.size == 0:
            last_local_date = '2019-02-01'
        else:
            last_local_date = str(last_local_date_sql.values[0])[:10]
        return last_local_date

    def _get_json_data(self, data_json_list):
        '''
        Return list of lists data with prices from Rosstat's json, e.g. [[344.43, 345.38, 349.53], [259.28, 255.82, 259.61], ..]
        '''
        output_list = []
        for row in data_json_list:
            output_list.append([x['db_value'] for x in row])
        return output_list

    def _get_json_dates(self, datetime_json_list):
        '''
        Return list of dates from Rosstat's json, e.g. [datetime.datetime(2020, 1, 1, 0, 0), ..]
        '''
        output_list = []
        for row in datetime_json_list:
            date_string = row['period'][:10]
            date_datetime = datetime.strptime(date_string, '%Y-%m-%d')
            output_list.append(date_datetime)
        return output_list

    def _get_gks_links_to_categoryids(self):
        '''
        Return dict with keys - local ids - and values - rosstat inner ids, e.g. {1: '10012', 2: '14334', ..}
        '''
        df = pd.read_csv(self.path_final_links, sep=';', index_col=0)
        dict_ = df[df.site_code == 'gks'].set_index('category_id')['site_link'].to_dict()
        return dict_

    def _returnRosstatInnerIds(self):
        '''
        Return list of inner rosstat ids, e.g. ['10012', '12231', ..]
        '''
        d = self.gks_links_to_categoryids
        list_ = list(d.values())
        return list_

    def construct_daterange_filter(self, dates: List) -> str:
        formatted_dates = list(map(lambda date: date + "+00%3A00%3A00%7C-56", dates))
        filter_string = self.construct_joined_string(formatted_dates)
        return filter_string

    def construct_joined_string(self, items):
        items_str = list(map(lambda item: str(item), items))
        return "%2C".join(items_str)

    def construct_url(self, date_start, date_end, category_ids) -> str:  # DONE
        dates = self.get_daterange_list(date_start, date_end)
        filter_1_0 = self.construct_daterange_filter(dates)
        filter_2_0 = 13035
        filter_3_0 = self.construct_joined_string(category_ids)
        return fr'https://showdata.gks.ru/x/report/277328/view/compound/?&filter_1_0={filter_1_0}&filter_2_0={filter_2_0}&filter_3_0={filter_3_0}&rp_submit=t&_=1620656798123'

    def _get_daterange_column(self, date_start="2019-02-01", date_end=datetime.now().date()):
        """
        Return daterange column for filling values in GKS raw dataframe
        :return: 
        datetime.date() column 
        """
        df_daterange = pd.DataFrame(index=pd.date_range(start=date_start, end=datetime.now().date()))
        df_daterange = df_daterange.reset_index().rename(columns={'index': 'date'})
        return df_daterange

    def get_daterange_list(self, date_start: str, date_end: str) -> List:
        date_range = pd.date_range(start=date_start, end=date_end, freq='MS').tolist()  # return first day of each month
        dates = [datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d") for date in date_range]
        return dates

    def get_df_raw(self, to_sql=True):

        if not self.is_parsing_needed:
            print('parsing is not needed')
            return pd.DataFrame()

        print('im here')

        date_start = self.date_end_local
        date_end = self.date_end_gks
        category_ids = self._returnRosstatInnerIds()
        gks_url = self.construct_url(category_ids=category_ids, date_start=date_start, date_end=date_end)
        r = requests.get(gks_url)
        data_json_list = r.json()['data']['reportData']['data']
        datetime_json_list = r.json()['headers']['reportHeaders']['col_header'][0]['children']
        data_list = self._get_json_data(data_json_list)
        dates_list = self._get_json_dates(datetime_json_list)
        df = pd.DataFrame(data=data_list, index=category_ids, columns=dates_list).transpose().stack().reset_index()
        df.columns = ['date', 'site_link', 'price_new']
        gks_links = self.gks_links_to_categoryids
        df.loc[:, 'category_id'] = df.site_link.apply(
            lambda x: list(gks_links.keys())[list(gks_links.values()).index(x)])
        df.loc[:, 'price_old'] = -1.0
        df.loc[:, 'miss'] = 0
        df.loc[:, 'site_code'] = 'gks'
        df_units = pd.read_sql(sql='SELECT * FROM parser_app_gks_units', con=self.engine)
        df_categories = pd.read_sql(sql='SELECT * FROM parser_app_category_titles', con=self.engine)
        df_types = pd.read_sql(sql='SELECT * FROM parser_app_category_types', con=self.engine)
        df = df.merge(df_units, left_on='category_id', right_on='category_id', how='left')
        df = df.merge(df_categories, left_on='category_id', right_on='category_id', how='left')
        df = df.merge(df_types, left_on='category_id', right_on='category_id', how='left')
        # add to sql

        df.to_sql(name='parser_app_pricesraw', con=self.engine, if_exists='append', index=False)
        return df

    def get_df_filled(self):  # TODO
        self.get_df_raw()
        df = pd.read_sql(sql='SELECT * FROM parser_app_pricesraw WHERE site_code="gks"', con=self.engine,
                         index_col='id')
        date_start = df.date.min()
        date_end = self._last_parsing_date
        dates_column = self._get_daterange_column(date_start=date_start, date_end=date_end)
        filled_df = df.groupby('category_id').apply(lambda x: x.merge(dates_column,
                                                                      left_on='date',
                                                                      right_on='date',
                                                                      how='right').ffill()).drop('category_id',
                                                                                                 axis=1).reset_index().drop(
            'level_1', axis=1)

        return filled_df