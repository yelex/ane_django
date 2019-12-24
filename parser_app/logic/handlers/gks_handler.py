import pandas as pd
import urllib
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, date
import numpy as np
from datetime import datetime
import time
from parser_app.logic.global_status import Global

df = Global().links
gks_id_list = df[df.site_code=='gks']['site_link'].values


# необходимые функции

def wspex(x):
    """
    White SPace EXclude
    :param x: string
    :return: string x without any whitespaces
    """
    return re.sub(u'\u200a', '', ''.join(x.split()))


def wspex_space(x):
    return re.sub(u'\u200a', '', ' '.join(str(x).split()))


def tofloat(s):
    return float(wspex(s.replace(',', '.')))


class SiteHandlerGks:

    def __init__(self):
        self.site_prefix = r'https://www.gks.ru/dbscripts/cbsd/DBInet.cgi?pl=1921002'
        self.description = r'Федеральная служба государственной статистики'
        self.site_id = 0
        self.pricelists = dict()
        self.site_code = 'gks'

    def extract_products(self, html):
        soup = BeautifulSoup(html, 'lxml')
        # print('soup', soup)
        products_tables = soup.findAll('table', {'class': 'OutTbl'})
        table_dict = dict()
        i = 0
        for products_table in products_tables:
            i += 1
            price_list_divs = products_table.find_all('tr')

            res = []
            if not price_list_divs:
                return []

            for price_elem in price_list_divs:
                tds = price_elem.find_all('td')
                # # print('tds()=', type(tds), tds[0], "&&&", tds[1])
                if tds[0].get('class') != 'TblShap' and tds[1].text != '' and wspex_space(tds[0].text):
                    # price_dict['gks_total'] = price_dict['gks_unit'] *
                    res.append(tofloat(tds[1].text))
            table_dict[i] = res
        # print("End extract")
        # print # str(x) for x in gks_id_list
        return table_dict

    def get_qry(self, year, month):
        return 'Pokazateli:1921001;okato:45000000;grtov:' + \
               ','.join([str(x) for x in gks_id_list]) + ';' + \
               'god:' + str(year) + ';' + \
               'period:' + ','.join([str(x) for x in list(range(1, month + 1))]) + ';'  #

    def process_table(self, year, month):
        url = 'https://www.gks.ru/dbscripts/cbsd/DBInet.cgi?pl=1921001'
        # print('qry = ', self.get_qry(year, month))
        values = {
            'rdLayoutType': 'Au',
            '_Pokazateli': 'on',
            '_okato': 'on',
            '_grtov': 'on',
            '_god': 'on',
            '_period': 'on',
            'a_Pokazateli': '1',
            'a_okato': '2',
            'a_grtov': '3',
            'Qry': self.get_qry(year, month),
            'QryGm': 'Pokazateli_z:1;okato_z:2;grtov_z:3;god_s:1;period_b:1;',  # '
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

        # # print(html)

        return self.extract_products(html)

    def get_qry_weekly(self, year):

        df = pd.read_csv(Global().gks_links, sep=';', index_col=0)

        list_grtov = df['site_link'].values

        list_period = [str(i) + str(datetime.now().year) for i in range(date(2019, 2, 1).isocalendar()[1] - 1,
                                                                        datetime.now().date().isocalendar()[1])]
        return 'Pokazateli:1921002;okato:45000000;grtov:' + \
               ','.join(str(i) for i in list_grtov) + ';' + \
               'god:' + year + ';' + \
               'period:' + ','.join(list_period) + ';'  #

    def process_table_weekly(self, year):
        url = 'https://www.gks.ru/dbscripts/cbsd/DBInet.cgi?pl=1921002'
        # print('qry = ', self.get_qry_weekly(year, month))
        values = {
            'rdLayoutType': 'Au',
            '_Pokazateli': 'on',
            '_okato': 'on',
            '_grtov': 'on',
            '_god': 'on',
            '_period': 'on',
            'a_Pokazateli': '1',
            'a_okato': '2',
            'a_period': '1',
            'a_grtov': '2',
            'Qry': self.get_qry_weekly(year),
            'QryGm': 'Pokazateli_z:1;okato_z:2;god_s:1;period_b:1;grtov_b:2;',  # '
            'QryFootNotes': ';',
            'YearsList': ';'.join(list(str(i) for i in range(2008, datetime.now().year + 1))) + ';',
            'tbl': 'Показать таблицу'
        }
        data = urllib.parse.urlencode(values, encoding='cp1251')
        # print(data)
        time.sleep(3)
        r = requests.post(url, data=data)
        r.encoding = 'cp1251'
        html = r.text

        # # print(html)

        return self.extract_products(html)

    def get_df_weekly(self):
        print('get data from GKS...')
        year = str(datetime.now().year)

        table = self.process_table_weekly(year)
        df_map = pd.read_csv(Global().gks_links, sep=';', index_col=0)[['cat_title']]

        df = pd.DataFrame(np.reshape(table[1], (len(table[1]) // 29, 29)),
                          index=[datetime.strptime('{}-W{}-1'.format(str(datetime.now().year), i), "%Y-W%W-%w") for i in
                                 range(date(2019, 2, 1).isocalendar()[1] - 1,
                                       date(2019, 2, 1).isocalendar()[1] - 1 + len(table[1]) // 29)],
                          columns=list(df_map.index))

        df = df.stack().reset_index().rename(columns={'level_0': 'date', 'level_1': 'category_id', 0: 'price_new'})
        df = df.pivot_table(index='date', columns='category_id', values='price_new').merge(
            pd.DataFrame(index=pd.date_range(start='2/1/2019',
                                             end=Global().date.strftime('%m/%d/%Y'))), left_index=True,
            right_index=True,
            how='right').fillna(method='ffill')

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
        print('completed!')
        return df

    def get_df_monthly(self):
        year = datetime.now().year
        month = datetime.now().month
        table = SiteHandlerGks().process_table(year, month)

        df = pd.DataFrame.from_dict(table)
        df = df.set_index(df.index + 1)

        df.loc[:, 'date'] = [date(day=1, month=i, year=2019) for i in range(1, len(df) + 1)]
        df.set_index('date', inplace=True)
        df = df.stack().reset_index()
        df = df.rename(columns={'level_1': 'category_id', 0: 'price_new'})
        df = df.pivot_table(index='date', columns='category_id', values='price_new').merge(
            pd.DataFrame(index=pd.date_range(start='2/1/2019',
                                             end=Global().date.strftime('%m/%d/%Y'))), left_index=True,
            right_index=True,
            how='right').fillna(method='ffill')
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
        df = df[df.category_id.isin([6, 12, 21, 33])]
        return df

    def get_df(self):
        df1 = SiteHandlerGks().get_df_weekly()
        df2 = SiteHandlerGks().get_df_monthly()
        df2 = df2[df2.date.isin(df1.date)]
        df = pd.concat([df1, df2])
        return df