import os
from typing import Dict, Union

import pandas as pd
import urllib
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time

from anehome.settings import DEVELOP_MODE
from parser_app.logic.global_status import Global
from parser_app.logic.handlers.tools import tofloat

df = Global().links
gks_id_list = df[df.site_code=='gks']['site_link'].values


class SiteHandlerGks:

    def __init__(self):
        self.site_prefix = r'https://www.gks.ru/dbscripts/cbsd/DBInet.cgi?pl=1921002'
        self.description = r'Федеральная служба государственной статистики'
        self.site_code = 'gks'

    def get_qry_weekly(self, year):

        if DEVELOP_MODE:
            df = pd.read_csv(
                os.path.join('parser_app', 'logic', 'description', 'gks_weekly_links.csv'),
                sep=';',
                index_col=0,
            )
        else:
            df = pd.read_csv(
                r'~/PycharmProjects/ane_django/parser_app/logic/description/gks_weekly_links.csv',
                sep=';',
                index_col=0,
            )

        list_grtov = df['site_link'].values

        if year == 2019:
            year_list = [str(i) + str(2019) for i in range(date(2019, 2, 1).isocalendar()[1] - 1,
                                                           53)]
        elif year != datetime.now().year and year != 2019:
            year_list = [str(i) + str(year) for i in range(date(year, 1, 1).isocalendar()[1] - 1,
                                                           53)]
        else:
            year_list = [str(i) + str(year) for i in range(date(year, 1, 1).isocalendar()[1],
                                                           datetime.now().date().isocalendar()[1])]

        return 'Pokazateli:1921002;okato:45000000;grtov:' + \
               ','.join(str(i) for i in list_grtov) + ';' + \
               'god:' + str(year) + ';' + \
               'period:' + ','.join(year_list) + ';'  #

    def process_table_weekly(self, years):
        url = 'https://www.gks.ru/dbscripts/cbsd/DBInet.cgi?pl=1921002'
        dict_years = {}
        for year in years:
            values = {
                'rdLayoutType': 'Au',
                '_Pokazateli': 'on',
                '_okato': 'on',
                '_grtov': 'on',
                '_god': 'on',
                '_period': 'on',
                'a_Pokazateli': '1',
                'a_okato': '2',
                'a_grtov': '1',
                'a_god': '2',
                'Qry': self.get_qry_weekly(year),
                'QryGm': 'Pokazateli_z:1;okato_z:2;grtov_s:1;god_s:2;period_b:1;',  # '
                'QryFootNotes': ';',
                'YearsList': ';'.join(list(str(i) for i in range(2008, int(year) + 1))) + ';',
                'tbl': 'Показать таблицу'
            }
            data = urllib.parse.urlencode(values, encoding='cp1251')

            time.sleep(3)
            r = requests.post(url, data=data)
            r.encoding = 'cp1251'
            html = r.text
            # print(html)
            extracted_weekly_products = self.extract_products_weekly(year, html)
            if extracted_weekly_products is not None:
                dict_years.update(extracted_weekly_products)

        return dict_years

    def extract_products_weekly(self, year, html) -> Union[None, Dict]:
        if 'Проблема доступа к БД' in html:
            # fixme - log - fatal - Проблема доступа к БД - no needed information
            print(f"extract_products_weekly -> Проблема доступа к БД - no needed information, return None")
            return None

        soup = BeautifulSoup(html, 'lxml')
        print('soup', soup)

        product_table = soup.find('table', {'class': 'OutTbl'})
        price_list_divs = product_table.find_all('tr')[2:]
        table_dict = dict()
        if year == 2019:
            i = date(2019, 2, 1).isocalendar()[1] - 1
        else:
            i = 0

        for price_elem in price_list_divs:
            i += 1

            tds = price_elem.find_all('td')[1:]
            res = [float(i.text.replace(',', '.')) for i in tds]
            table_dict[str(i) + str(year)] = res

        return table_dict

    def get_df_weekly(self):
        list_year = [i for i in range(2019, datetime.now().year + 1)]
        # print('list_year: ', list_year)
        table_dict = self.process_table_weekly(list_year)

        df = pd.DataFrame().from_dict(table_dict, orient='index')
        # print(df)
        df_map = pd.read_csv(Global().gks_links, sep=';',
                             index_col=0)[['cat_title']]
        if len(df) <= len(range(date(2019, 2, 1).isocalendar()[1] - 1, 53)):
            index_y_full = [datetime.strptime('{}-W{}-1'.format(str(2019), i), "%Y-W%W-%w") for i in
                            range(date(2019, 2, 1).isocalendar()[1] - 1,
                                  date(2019, 2, 1).isocalendar()[1] - 1 + len(df))]

        else:
            index_y_19 = [datetime.strptime('{}-W{}-1'.format(str(2019), i), "%Y-W%W-%w") for i in
                          range(date(2019, 2, 1).isocalendar()[1] - 1, 52)]
            index_y_another = []
            for year in range(2020, datetime.now().year + 1):
                if year == datetime.now().year:
                    index_y_another = index_y_another + [datetime.strptime('{}-W{}-1'.format(str(year), i), "%Y-W%W-%w")
                                                         for i in range(date(year, 1, 1).isocalendar()[1],
                                                                        Global().date.isocalendar()[1])]
                else:
                    index_y_another = index_y_another + [datetime.strptime('{}-W{}-1'.format(str(year), i), "%Y-W%W-%w")
                                                         for i in range(date(year, 1, 1).isocalendar()[1], 53)]
            index_y_full = index_y_19 + index_y_another
            # print(index_y_full)
        # print(index_y_full)

        df.columns = list(df_map.index)
        df.index = index_y_full[:len(df.index)]

        df = df.stack().reset_index().rename(columns={'level_0': 'date', 'level_1': 'category_id', 0: 'price_new'})
        df = df.pivot_table(index='date', columns='category_id',
                            values='price_new').merge(pd.DataFrame(index=pd.date_range(start='2/1/2019',
                                                                                       end=Global().date.strftime(
                                                                                           '%m/%d/%Y'))),
                                                      left_index=True, right_index=True, how='right').fillna(
            method='ffill')

        df = df.stack().reset_index().rename(columns={'level_0': 'date', 'level_1': 'category_id', 0: 'price_new'})
        df.loc[:, 'type'] = 'food'
        df1 = pd.read_csv(Global().example_shot, index_col=0)
        df = df.merge(df1[['category_id', 'category_title']].drop_duplicates(), left_on='category_id',
                      right_on='category_id')
        keys = list(range(1, 34))
        values = gks_id_list
        dictionary = dict(zip(keys, values))
        df = df.merge(pd.Series(dictionary).rename('site_link'), left_on='category_id', right_index=True)
        df.loc[:, 'site_title'] = df.loc[:, 'category_title']
        df.loc[:, 'site_code'] = 'gks'
        df2 = pd.read_csv(Global().path_sfb, sep=';')
        df = df.merge(df2[['id', 'unit']], left_on='category_id', right_on='id').drop('id', axis=1).rename(
            columns={'unit': 'site_unit'})
        df.loc[:, 'price_old'] = -1.0
        df.loc[:, 'miss'] = 0
        return df

    def get_qry_monthly(self, year, month):  # 1-monthly

        return 'Pokazateli:1921001;okato:45000000;grtov:' + \
               ','.join([str(x) for x in gks_id_list]) + ';' + \
               'god:' + str(year) + ';' + \
               'period:' + ','.join([str(x) for x in list(range(1, month + 1))]) + ';'  #

    def process_table_monthly(self, year, month):  # 2-monthly
        url = 'https://www.gks.ru/dbscripts/cbsd/DBInet.cgi?pl=1921001'
        # print('qry = ', self.get_qry(year, month))
        if month == 2 and year == 2020:
            year = 2019
            month = 12
        values = {
            'rdLayoutType': 'Au',
            '_Pokazateli': 'on',
            '_okato': 'on',
            '_grtov': 'on',
            '_god': 'on',
            '_period': 'on',
            'a_Pokazateli': '1',
            'a_okato': '2',
            'a_god': '1',
            'a_grtov': '2',
            'Qry': self.get_qry_monthly(year, month),
            'QryGm': 'Pokazateli_z:1;okato_z:2;god_s:1;grtov_s:2;period_b:1;',  # '
            'QryFootNotes': ';',
            'YearsList': '1995;1996;1997;1998;1999;2000;2001;2002;2003;2004;2005;2006;2007;2008;2009;2010;2011;2012;2013;2014;2015;2016;2017;2018;2019;',
            'tbl': 'Показать таблицу'
        }
        data = urllib.parse.urlencode(values, encoding='cp1251')
        # print(data)
        time.sleep(3)
        r = requests.post(url, data=data)
        r.encoding = 'cp1251'
        html = r.text

        return self.extract_products_monthly(html)

    def extract_products_monthly(self, html):
        soup = BeautifulSoup(html, 'lxml')
        # print('soup', soup)
        table = soup.find('table', {'class': 'OutTbl'})
        trs = table.find_all('tr')[2:]
        # print('trs[0]: ', trs[0])
        table_dict = dict()
        i = 0

        for tr in trs:
            i += 1
            res = []
            tds = tr.find_all('td', {'align': 'right'})
            # print(tds)
            # print('tds()=', type(tds), tds[0], "&&&", tds[1])
            for td in tds:
                res.append(tofloat(td.text))
            table_dict[i] = res
        # print("End extract")
        # print # str(x) for x in gks_id_list
        return table_dict

    def get_df_monthly(self, year):

        if year != datetime.now().year or datetime.now().month == 1:
            month = 12
            end_date = f'12/31/{year}'
        else:
            month = datetime.now().month - 1
            end_date = Global().date.strftime('%m/%d/%Y')

        table = SiteHandlerGks().process_table_monthly(year, month)
        # print(table)
        df = pd.DataFrame.from_dict(table).transpose()
        df.columns = list(range(1, len(df.columns) + 1))
        #         print(df)
        df = df.set_index(df.index + 1)

        df.loc[:, 'date'] = [date(day=1, month=i, year=year) for i in range(1, len(df) + 1)]
        df.set_index('date', inplace=True)

        df = df.stack().reset_index()
        df = df.rename(columns={'level_1': 'category_id', 0: 'price_new'})
        df_time = pd.DataFrame(index=pd.date_range(start='2/1/2019', end=end_date))
        df = df.pivot_table(index='date', columns='category_id', values='price_new').merge(df_time, left_index=True,
                                                                                           right_index=True,
                                                                                           how='right').fillna(
            method='ffill')
        df = df.stack().reset_index().rename(columns={'level_0': 'date', 'level_1': 'category_id', 0: 'price_new'})
        # print(df)
        df.loc[:, 'type'] = 'food'
        df1 = pd.read_csv(Global().example_shot, index_col=0)
        df = df.merge(df1[['category_id', 'category_title']].drop_duplicates(), left_on='category_id',
                      right_on='category_id')
        keys = list(range(1, 34))
        values = gks_id_list
        dictionary = dict(zip(keys, values))
        df = df.merge(pd.Series(dictionary).rename('site_link'), left_on='category_id', right_index=True)
        df.loc[:, 'site_title'] = df.loc[:, 'category_title']
        df.loc[:, 'site_code'] = 'gks'
        df2 = pd.read_csv(Global().path_sfb, sep=';')
        df = df.merge(df2[['id', 'unit']], left_on='category_id', right_on='id').drop('id', axis=1).rename(
            columns={'unit': 'site_unit'})
        df.loc[:, 'price_old'] = -1.0
        df.loc[:, 'miss'] = 0
        df = df[df.category_id.isin([6, 12, 21, 33])]
        return df

    def get_df(self):
        df_week = SiteHandlerGks().get_df_weekly()
        df_month = pd.DataFrame()
        years = list(range(2019, datetime.now().year + 1))
        for year in years:
            temp_df = SiteHandlerGks().get_df_monthly(year)
            df_month = df_month.append(temp_df)
        df_month = df_month[df_month.date.isin(df_week.date)]
        df = pd.concat([df_week, df_month])
        return df
