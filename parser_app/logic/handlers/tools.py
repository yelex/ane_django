from bs4 import BeautifulSoup
import pandas as pd
import re
import random
import requests
import time
import os
from threading import Timer  # для автозапуска
import smtplib
import datetime
from datetime import date
import numpy as np
from tqdm import tqdm
import difflib
import ssl
from stem.control import Controller
from stem import Signal

from parser_app.logic import gloabal_paths


ssl._create_default_https_context = ssl._create_unverified_context


class perpetualTimer:

    def __init__(self, t, hFunction):
        self.t = t  # t
        self.hFunction = hFunction
        self.thread = Timer(0, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = Timer(self.t, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


def filter_flag(id_n, text):  # id_n-номер категории (1..33), pro=True если учитывать слова "за", False - иначе
    path_sfb = os.path.join(gloabal_paths.base_dir, 'description', 'urls.csv')
    sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
    row = sfb_df.loc[[id_n]]
    keyword = row['keyword'].values[0]
    pattern_pro = row['keywords_pro'].values[0]
    pattern_cons = row['keywords_cons'].values[0]

    match_kwrd = re.search(str(keyword), text, flags=re.IGNORECASE)
    match_pro = re.search(str(pattern_pro), text, flags=re.IGNORECASE)
    match_cons = re.search(str(pattern_cons), text, flags=re.IGNORECASE)

    if match_kwrd or keyword in ['хлеб', 'рыба']:
        if type(pattern_pro) is float and type(pattern_cons) is float:
            flag = True
        elif type(pattern_pro) is float and type(pattern_cons) is not float:
            flag = True if not match_cons else False
        elif type(pattern_pro) is not float and type(pattern_cons) is float:
            flag = True if match_pro else False
        elif type(pattern_pro) is not float and type(pattern_cons) is not float:
            flag = True if match_pro and not match_cons else False
        else:
            ValueError('Переопределите pattern_pro и/или pattern_cons')
    else:
        flag = False

    return flag


def wspex(x):
    return re.sub(u'\u200a', '', ''.join(x.split()))


def list_html(text):
    return (text.split())


def wspex_space(x):
    return re.sub(u'\u200a', '', ' '.join(str(x).split()))


def tofloat(s):
    return float(wspex(s.replace(',', '.')))


def find_float_number(str):
    str = wspex(str)
    sr = re.findall(r"[-+]?\d*[.,]\d+|\d+", str)
    if sr:
        return float(sr[0].replace(',', '.'))
    else:
        return None


def checkIP():
    ip = requests.get('http://checkip.dyndns.org').content
    soup = BeautifulSoup(ip, 'html.parser')
    print(soup.find('body').text)


def clever_sleep(mu=5, sigma=0.3):
    nmb = sigma * np.random.randn() + mu
    print(nmb)
    time.sleep(nmb)


def get_proxy(link, get_new=False, get_list=False):
    with Controller.from_port(port=9051) as controller:
        controller.authenticate('mypassword')
        controller.signal(Signal.NEWNYM)
    proxies = {
        'http': 'socks5h://127.0.0.1:9060',
        'https': 'socks5h://127.0.0.1:9060'
    }
    return proxies


def strsim(a, b):
    return wspex_space(a).lower() == wspex_space(b).lower()


def send_mail(message, sender='ane_debug@mail.ru', to='evseev_alexey94@bk.ru'):
    smtp_server = 'smtp.mail.ru'
    smtp_port = 465
    smtp_pasword = 'ane_coworking'
    msg = message.encode('utf-8').strip()
    mail_lib = smtplib.SMTP_SSL(smtp_server, smtp_port)
    mail_lib.login(sender, smtp_pasword)
    mail_lib.sendmail(sender, to, msg)
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print('e-mail has been sent {}'.format(date))


def fill_df(df):
    df.loc[:, 'date'] = pd.to_datetime(df.loc[:, 'date'], format='%Y-%m-%d')
    df = df.drop_duplicates(subset=['date', 'site_title', 'site_link']).reset_index().reset_index().drop(
        columns='id').rename(columns={'index': 'id'}).set_index('id')

    df.price_new = df.price_new.astype(float)
    start_date = df.date.values.min()
    end_date = df.date.values.max()
    daterange = pd.date_range(start=start_date, end=end_date)
    df.loc[:, 'unq'] = df.category_id.astype(str) + df.site_link
    pvt_before = pd.pivot_table(df, columns='unq', index='date', values='price_new')
    n_days_limit = 150
    pvt_after = pvt_before.merge(pd.Series(index=daterange, data=np.nan, name=1), left_index=True, \
                                 right_index=True, how='right').iloc[:, :-1].apply(
        lambda x: x.fillna(method='ffill', limit=n_days_limit))

    df = df.drop('price_new', axis=1).merge(pvt_after.transpose().stack().rename('price_new'), \
                                            left_on=['unq', 'date'], right_index=True, how='right')
    df.loc[:, 'miss'] = df.loc[:, 'site_title'].isna().astype(int)
    df = df.sort_values(['unq', 'date'])
    df = df.groupby('unq').transform(lambda x: x.fillna(method='ffill'))
    df = df.reset_index().drop('id', axis=1).reset_index().rename(columns={'index': 'id'}).set_index('id')
    df.loc[:, 'category_id'] = df.category_id.astype(int)
    df.loc[:, 'price_old'] = df.price_old.astype(float)
    df.loc[:, 'nsprice_f'] = (df.price_old == -1.0).replace(False, np.nan) * (df.price_new).apply(
        lambda x: np.nan if x == 0 else x)
    df = df.groupby('site_link').apply(lambda x: x.fillna(method='ffill', limit=n_days_limit))
    df.loc[df.nsprice_f.isna(), 'nsprice_f'] = df[df.nsprice_f.isna()].price_old
    # df = df.drop('unq', axis=1)
    return df


def text_diff(case_a, case_b):
    output_list = [li for li in difflib.ndiff(case_a, case_b) if li[0] != ' ']

    return ''.join([i[-1] for i in output_list])


def pack_to_gramm(string):  # перевод в граммы для (50×2г)
    pattern_1 = re.compile('\d+\s{0,1}(пак){0,1}\s{0,1}(?:\*|×|x|х)')
    pattern_2 = re.compile('(?:\*|×|x|х)\s{0,1}\d+\,{0,1}\d*\s*г')
    pattern_3 = re.compile('\d+(?:\,|\.){0,1}\d*\s*г(?:\*|×|x|х)')
    pattern_4 = re.compile('(?:\*|×|x|х)\s{0,1}\d+\s{0,1}(пак){0,1}')

    if re.search(pattern_1, string) != None and re.search(pattern_2, string) != None:
        return str(int(wspex(re.search('\d+', ((re.search(pattern_1, string)[0])[:-1]))[0])) * tofloat(
            re.search(pattern_2, string)[0][1:-1])) + 'г'
    if re.search(pattern_3, string) != None and re.search(pattern_4, string) != None:
        return str(int(wspex(re.search('\d+', ((re.search(pattern_4, string)[0])))[0])) * tofloat(
            wspex(re.search(pattern_3, string)[0])[:-2])) + 'г'


# price_in_basket

sfb = pd.read_csv(gloabal_paths.path_sfb, sep=';')


def price_coef(id_n, string_unit):  # основано на весах 33 категорий условного минимального набора товаров и услуг
    # столбик весов - перевод в нужные единицы веса - перевод в стоимость через коэффициент
    # print(string_unit)
    global sfb
    kg_units = ['кг', 'kg', 'килограмм']
    g_units = ['г', 'g', 'грамм', 'граммов', 'гр']  # в кг
    litre_units = ['л', 'l', 'литр', 'литров', 'литра']
    ml_units = ['мл', 'ml', 'миллилитров', 'миллилитра']
    amount = float(re.search('\d+(\.\d*){0,1}', string_unit)[0])
    unit = re.search('[а-яa-z]+', string_unit)[0]

    if unit in g_units or unit in ml_units:
        coeff = 1000 / amount
    elif unit in kg_units or unit in litre_units:
        coeff = 1 / amount
    elif unit == 'шт':
        coeff = 10 / amount
    else:
        raise ValueError('Unit {} from string_unit {} is unknown'.format(unit, string_unit))
    coeff = coeff * sfb[sfb.id == id_n].req_amount.iloc[0]
    return coeff / 12


def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)

    percentile_.__name__ = 'percentile_%s' % n
    return percentile_


def get_basket_df(df_gks, df_retail, date=date(2019, 3, 1)):
    # print('get basket df...')
    df_gks.loc[:, 'nsprice_f'] = df_gks.loc[:, 'price_new']
    df_gks.loc[:, 'date'] = pd.to_datetime(df_gks.loc[:, 'date'], format='%Y-%m-%d')
    df_gks = df_gks.drop_duplicates(subset=['date', 'site_title', 'site_link']).reset_index(drop=True)
    # онлайн-проды
    # df_retail = df_retail.drop('id', axis=1)
    df_retail = df_retail.drop('level_0', axis=1)
    df_retail.loc[:, 'date'] = pd.to_datetime(df_retail.date)
    df = pd.concat([df_gks, df_retail], join='inner')

    df = df.drop_duplicates(subset=['date', 'site_title', 'site_link']).reset_index(drop=True)

    df_new = df.loc[df.date >= pd.Timestamp(date), :]
    grouped = df_new.groupby(['category_id', 'site_code', 'site_link']).nunique()[['date']]
    grouped = grouped.loc[grouped.date == max(grouped.date), :]
    links = grouped.index.get_level_values(level=2)
    # подготовленный датафрейм (только те товары, которые наблюдались с 1 июля 2019 и по сегодня)
    df_new = df_new[df_new.site_link.isin(links)]
    # weight

    piece_units = ['шт', 'штук', 'штуки', 'штука', 'пак', 'пакетиков', 'пак']
    kg_units = ['кг', 'kg', 'килограмм']  # оставить в граммах
    gram_units = ['г', 'g', 'грамм', 'граммов', 'гр']  # в кг
    litre_units = ['л', 'l', 'литр', 'литров', 'литра']
    ml_units = ['мл', 'ml', 'миллилитров', 'миллилитра']
    tenpiece_units = ['10 шт', '10 шт.', '10шт', '10шт.', 'десяток', 'дес.']

    kg_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{1,4})\s*(?:' + r'|'.join(kg_units) + r')'
    g_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{1,4})\s*(?:' + r'|'.join(gram_units) + r')'
    l_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{1,4})\s*(?:' + r'|'.join(litre_units) + r')'
    ml_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{1,4})\s*(?:' + r'|'.join(ml_units) + r')'
    piece_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{1,4})\s*(?:' + r'|'.join(piece_units) + r')'
    tenpiece_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{1,4})\s*(?:' + r'|'.join(tenpiece_units) + r')'

    patterns = [piece_pattern, tenpiece_pattern, kg_pattern, g_pattern, l_pattern, ml_pattern]
    df_new['weight'] = None

    for title in tqdm(df_new.site_title.unique()):
        for pattern in patterns:
            match = re.search(pattern, title.lower())
            if match:
                df_new.loc[df_new.site_title == title, 'weight'] = match[0]
    df_new.loc[df_new.weight.isna(), 'weight'] = df_new.loc[df_new.weight.isna(), 'site_unit']
    df_new.loc[df_new.site_unit.isin(['за 1 кг', 'кг', 'за 100 г']), 'weight'] = df_new.loc[
        df_new.site_unit.isin(['за 1 кг', 'кг', 'за 100 г']), 'weight'].apply(lambda x: wspex(x).replace('за', ''))
    df_new.loc[df_new.weight == 'кг', 'weight'] = '1кг'
    df_new.loc[df_new.site_unit == 'кг', 'weight'] = '1кг'

    # weight only

    df_new.loc[:, 'weight'] = df_new.weight.apply(lambda x: wspex(x.replace('\xa0', '')) if x is not None else x)

    df_new.loc[:, 'weight'] = df_new.weight.apply(lambda x: x.replace(',', '.') if ',' in x else x)
    pattern1 = re.compile('\d+\s{0,1}(пак){0,1}\s{0,1}(?:\*|×|x|х)\s{0,1}\d+\,{0,1}\d*\s*г')
    pattern2 = re.compile('\d+(?:\,|\.){0,1}\d*\s*г(?:\*|×|x|х)\s{0,1}\d+\s{0,1}(пак){0,1}')
    df_new.loc[:, 'weight'] = df_new.apply(
        lambda x: pack_to_gramm(x['site_title'])
        if re.search(pattern1, x['site_title']) != None or re.search(pattern2,x['site_title']) is not None
        else x['weight'], axis=1
    )

    dict_pack = {'25пак': '50г', '20пак': '80г', '100пак': '200г', 'л': '1л', '010шт': '10шт.',
                 '2019кг': '1кг', '110шт': '10шт', '210шт': '10шт'}

    df_new.loc[:, 'weight'] = df_new.weight.replace(dict_pack)
    df_new.loc[(df_new.weight == '4l') & (df_new.type == 'food'), 'weight'] = df_new.loc[
        (df_new.weight == '4l') & (df_new.type == 'food'), 'site_unit'].apply(lambda x: wspex(x).replace(',', '.'))
    df_new.loc[df_new.site_title == 'Соль поваренная пищевая каменная помол №1', 'weight'] = '1кг'
    df_new = df_new[df_new.site_title.str.contains('Огурцы длинноплодные шт') == False]
    df_new = df_new[df_new.weight != '1шт']
    non_sht = df_new.loc[
        (df_new.site_title.str.contains(re.compile('Яйц(?:о|а)')) == False) & (df_new.weight.str.contains('шт')) & (
                df_new.type == 'food')].site_link.unique()
    df_new = df_new[df_new.site_link.isin(non_sht) == False]
    df_new.loc[:, 'coef'] = None
    # df_new.loc[df_new.nsprice_f==-1.0,'nspices_f']=0
    for id_n in tqdm(df_new.category_id.unique()):
        for unit in df_new.loc[df_new.category_id == id_n].weight.unique():
            df_new.loc[(df_new.category_id == id_n) & (df_new.weight == unit), 'coef'] = price_coef(id_n, unit)

    print('here!')
    df_new['price_bsk'] = df_new.loc[:, 'coef'] * df_new.loc[:, 'nsprice_f']  # поменять на регулярные цены
    print('pass 1')
    df_new['price_bsk'] = [float(x) for x in df_new['price_bsk'].fillna(-1.0)]
    print('pass 2')
    df_new = df_new.drop_duplicates(subset=['date', 'site_title', 'site_code'])
    print('pass')

    print(df_new.columns)

    def percentile(n):
        def percentile_(x):
            return np.percentile(x, n)

        percentile_.__name__ = 'percentile_%s' % n
        return percentile_

    # for key, rows in df_new[df_new.site_code == 'gks'].groupby(['date']):
    #     print(key)
    #     print(rows)
    #     print(np.sum(list(rows['price_bsk'])))
    #     print()
    # )
    print('pass 3')

    # print(df_new[df_new.site_code != 'gks']
    #         .groupby(['date', 'category_id'])
    #         .aggregate(lambda x: np.percentile(x, 25)))
    #
    # basket_df['online_price'] = (
    #     df_new[df_new.site_code != 'gks']
    #         .groupby(['date', 'category_id'])
    #         .aggregate(lambda x: np.percentile(x, 25))
    #         .groupby(level=0)
    #         .apply(lambda x: np.sum(list(x['price_bsk'])))
    #         # .sum()['price_bsk']
    # )

    basket_df = pd.DataFrame(columns=['date', 'gks_price', 'online_price'])
    # buffer = {'date': [], 'gks_price': [], }
    for date, rows in df_new.groupby('date'):
        # print(rows)
        # print(rows[rows['site_code'] == 'gks'])
        # print(type(rows[rows['site_code'] == 'gks']))
        sum_price_gks = rows[rows['site_code'] == 'gks']['price_bsk'].sum()
        sum_price_online = rows[rows['site_code'] != 'gks']['price_bsk'].sum()
        basket_df = basket_df.append(
            {
                'date': date,
                'gks_price': sum_price_gks,
                'online_price': sum_price_online,
            },
            ignore_index=True,
        )

    # basket_df['gks_price'] = (
    #     df_new[df_new.site_code == 'gks']
    #         .groupby(['date'])
    #         .apply(lambda x: np.sum(list(x['price_bsk'])))
    #
    # basket_df['online_price'] = (
    #     df_new[df_new.site_code != 'gks']
    #         .groupby(['date'])
    #         .apply(lambda x: np.sum(list(x['price_bsk'])))
    # )
    #
    # print(basket_df)
    # print(basket_df.columns)
    # print('pass 4')
    # basket_df = basket_df.reset_index().reset_index().rename(columns={'index': 'id'}).set_index('id')

    print('completed!')
    return basket_df
