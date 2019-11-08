
from bs4 import BeautifulSoup
import pandas as pd
import re
import random
import requests
import time
import os
from parser_app.logic.global_status import Global
from selenium import webdriver
from threading import Timer  # для автозапуска
from fake_useragent import UserAgent
import smtplib
import datetime

class perpetualTimer():

   def __init__(self, t, hFunction):
      self.t = t  # t
      self.hFunction = hFunction
      self.thread = Timer(0, self.handle_function)

   def handle_function(self):
      self.hFunction()
      self.thread = Timer(self.t,self.handle_function)
      self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()

def filter_flag(id_n, text):  # id_n-номер категории (1..33), pro=True если учитывать слова "за", False - иначе
    path_sfb = os.path.join(Global.base_dir, r'description\urls.csv')
    sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
    row = sfb_df.loc[[id_n]]
    keyword = row['keyword'].values[0]
    pattern_pro = row['keywords_pro'].values[0]
    pattern_cons = row['keywords_cons'].values[0]

    match_kwrd = re.search(str(keyword), text, flags=re.IGNORECASE)
    match_pro = re.search(str(pattern_pro), text, flags=re.IGNORECASE)
    match_cons = re.search(str(pattern_cons), text, flags=re.IGNORECASE)

    if match_kwrd or keyword in ['хлеб','рыба']:
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

    return (flag)

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

def get_proxy(link):
    while True:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        driver = webdriver.Chrome(executable_path = Global().path_chromedriver, options=options)
        driver.get("https://hidemyna.me/ru/proxy-list/?maxtime=300&ports=3128..")
        while True:
            time.sleep(1)
            if "maxtime" in driver.page_source:
                ip_list = re.findall(r'\d{2,3}[.]\d{2,3}[.]\d{2,3}[.]\d{2,3}', driver.page_source)
                # print ('ip_list: ',ip_list)
                break
        ua = UserAgent()
        header = {'User-Agent': str(ua.chrome)}
        driver.quit()
        html = None
        for it in range(5):
            print('it =', it)
            proxy = random.choice(ip_list[1:]) + ":3128"
            proxies = {
              'https': 'https://{}'.format(proxy),
            }
            try:
                if 'okey' in link:
                    cookie = \
                        r"_ga=GA1.2.1743913103.1529597174; _ym_uid=1529597174997115265; _gac_UA-58508147-1=1.1529607077.EAIaIQobChMItoj" + \
                        r"f2rLl2wIVjIeyCh2stAAuEAAYASAAEgLCdvD_BwE; _gid=GA1.2.654182099.1529924428; _ym_d=1529924428; _ym_isad=1; _ym_" + \
                        r"visorc_27891822=w; storeGroup=msk1; ffcId=13151; WC_SESSION" + \
                        r"_ESTABLISHED=true; WC_PERSISTENT=3EJGXVtLqH2nPYh%2FBwXZCgqDdro%3D%0A%3B2018-06-26+21%3A22%3A20.903_1530037336" + \
                        r"387-297473_10151; WC_AUTHENTICATION_-1002=-1002%2CshqcDFo2KYvSQjMlws143PZaUdk%3D; WC_ACTIVEPOINTER=-20%2C10151;" + \
                        r"WC_GENERIC_ACTIVITYDATA=[876474606%3Atrue%3Afalse%3A0%3ACLFoHnycXg06Qmg4qmgtx7v6u%2Bc%3D][com.ibm.commerce" + \
                        r".context.audit.AuditContext|1530037336387-297473][com.ibm.commerce.store.facade.server.context.StoreGeoCodeContext" + \
                        r"|null%26null%26null%26null%26null%26null][CTXSETNAME|Store][com.ibm.commerce.context.globalization.Globalization" + \
                        r"Context|-20%26RUB%26-20%26RUB][com.ibm.commerce.catalog.businesscontext.CatalogContext|12051%26null%26false%26false" + \
                        r"%26false][com.ibm.commerce.context.ExternalCartContext|null][com.ibm.commerce.context.base.BaseContext|10151%26-" + \
                        r"1002%26-1002%26-1][com.ibm.commerce.context.experiment.ExperimentContext|null][com.ibm.commerce.context.entitlement" + \
                        r".EntitlementContext|4000000000000000003%264000000000000000003%26null%26-2000%26null%26null%26null][com.ibm." + \
                        r"commerce.giftcenter.context.GiftCenterContext|null%26null%26null]; isNative=1; searchTermHistory=%7C%D1%81%D0%" + \
                        r"BC%D0%B5%D1%82%D0%B0%D0%BD%D0%B0; gtmListKey=GTM_LIST_SEARCH; tmr_detect=1%7C1530037350771"

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                        'Cookie': cookie,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                        'Cache-Control': 'max-age=0'}
                    html = requests.get(link, headers=headers, proxies=proxies).content
                else:
                    html = requests.get(link, proxies=proxies, headers=header).content
                soup = BeautifulSoup(html, 'lxml')

                if html is not None and 'We have detected' not in soup.text:
                    break
            except:
                continue

        if html is not None:
            break
        else:
            continue
    print('good proxy: {}'.format(proxy))
    driver.quit()
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
    df.loc[:, 'price_old'] = df.loc[:, 'price_old'].apply(lambda x: -1.0 if x == '' else x)
    df.loc[:, 'date'] = pd.to_datetime(df.loc[:, 'date'], format='%Y-%m-%d')

    df = df.drop_duplicates(subset=['date', 'site_title', 'site_link']).reset_index(drop=True)
    df.tail()
    df.date = pd.to_datetime(df.date)

    df.price_new = df.price_new.astype(float)
    start_date = df.date.values.min()
    end_date = df.date.values.max()
    daterange = pd.date_range(start=start_date, end=end_date)
    pvt_before = df.pivot_table(columns='site_link', index='date', values='price_new')
    n_days_limit = 150
    pvt_after = pvt_before.merge(pd.Series(index=daterange, data=np.nan, name=1), left_index=True, \
                                 right_index=True, how='right').iloc[:, :-1].apply(
        lambda x: x.fillna(method='ffill', limit=n_days_limit))

    df = df.drop('price_new', axis=1).merge(pvt_after.transpose().stack().rename('price_new'), \
                                            left_on=['site_link', 'date'], right_index=True, how='right')

    df.loc[:, 'miss'] = df.loc[:, 'site_title'].isna().astype(int)
    df.loc[:, 'price_old'] = df.loc[:, 'price_old'].apply(lambda x: -1.0 if x == None else x)

    df = df.reset_index().drop('index', axis=1)
    df = df.sort_values(['site_link', 'date'])
    df.loc[:, 'URL'] = df.loc[:, 'site_link']
    df = df.groupby('URL').transform(lambda x: x.fillna(method='ffill'))
    df = df.reset_index().drop('index', axis=1)
    df.category_id = df.category_id.astype(int)
    df.loc[:, 'nsprice_f'] = ((df.price_old == -1.0).replace(False, np.nan)) * (df.price_new).apply(
        lambda x: np.nan if x == 0 else x)
    df = df.groupby('site_link').apply(lambda x: x.fillna(method='ffill', limit=n_days_limit))
    df.loc[df.nsprice_f.isna(), 'nsprice_f'] = df.loc[df.nsprice_f.isna(), 'price_old']
    df.nsprice_f = df.nsprice_f.astype(float)
    df = df.drop_duplicates()
    return df
    path_db2 = r'D:\ANE_django\db.sqlite3'
    con2 = sqlite3.connect(path_db2)
    df.to_sql(name='parser_app_pricesprocessed', con=con2, if_exists='replace', index=False)