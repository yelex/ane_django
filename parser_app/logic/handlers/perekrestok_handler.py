from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from parser_app.logic.handlers.tools import clever_sleep, filter_flag, get_proxy, tofloat, wspex_space, wspex
from parser_app.logic.global_status import Global
from tqdm import tqdm
import re
import time
from fake_useragent import UserAgent
import ssl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc

ssl._create_default_https_context = ssl._create_unverified_context

class PerekrestokHandler():

    def extract_products(self, is_proxy = True):
        if is_proxy == True:
            proxies = get_proxy('https://www.perekrestok.ru/')
        else:
            proxies = None
        start_time = datetime.now().minute
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])
        fail_array = []
        path_sfb = os.path.join(Global.base_dir, r'description/urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
        hrefs = sfb_df[sfb_df.fillna('')['URL'].str.contains('vprok')]['URL'].values
        hrefs = [href for href in hrefs if type(href) is not float]
        # print(hrefs)
        id_n=0

        for href in tqdm(hrefs):

            n_items_before = len(res)

            category_titles = sfb_df[sfb_df.fillna('')['URL'].str.contains('perekrestok')]['cat_title']


            try:
                html = requests.get(href, proxies=proxies).content
            except:
                proxies = get_proxy(href)
                html = requests.get(href, proxies=proxies).content

            soup = BeautifulSoup(html, 'html.parser')
            print(soup)
            try:
                helper_div = soup.find('div', {'class': 'xf-sort__total js-list-total'})
            except:
                print('WARNING!!! helper_div in {} has not found'.format(href))
                fail_array.append(href)
                continue
            total_amount = int(helper_div.find('span', {'class': 'js-list-total__total-count'}).text)
            print('\n' + category_titles.iloc[id_n] + '... товаров в категории: ' + str(total_amount))
            page = 0

            id_n += 1

            # print('  total_amount: {}'.format(total_amount))
            n_elem = 0
            n_elem_out = 0
            while n_elem<total_amount-n_elem_out:
                # print('n_elem: {} total_amount: {}'.format(n_elem, total_amount))

                total_amount = int(helper_div.find('span', {'class': 'js-list-total__total-count'}).text)

                page+=1
                if href[-1]=='?':
                    href_i='{}page={}'.format(href,page)
                else:
                    href_i='{}&page={}'.format(href,page)
                # print('\tgetting page: {}'.format(href_i,page))
                try:
                    html_i = requests.get(href_i, proxies=proxies).content
                    #print('im here')
                except:
                    proxies = get_proxy(href_i)
                    html_i = requests.get(href_i, proxies=proxies).content
                soup = BeautifulSoup(html_i, 'html.parser')
                products_div = soup.find('div', {'class': 'js-catalog-wrap'})
                price_list = products_div.find_all('div', {'class': 'xf-product js-product'})
                # print('price_list:{}\n\n'.format(products_div,price_list))
                n_elem_out += len(products_div.find_all('div', {'class': re.compile(r'\w*ot-activ\w+')}))
                # print(n_elem_out)
                for price_elem in price_list:
                    n_elem+=1
                    price_dict = dict()
                    price_dict['date']=Global().date
                    price_dict['site_code'] = 'perekrestok'
                    price_dict['category_id'] = id_n
                    price_dict['category_title'] = category_titles.iloc[id_n-1]
                    aref = price_elem.find('div', {'class': 'xf-product__title xf-product-title'}).\
                        find('a', {'class': 'xf-product-title__link js-product__title'})

                    price_dict['site_title'] = aref.text.strip()

                    if filter_flag(id_n,price_dict['site_title'])==False:
                        # print("skipped position: {}".format(price_dict['site_title']))
                        continue
                    cost_div = price_elem.find('div', {'class': 'xf-product__cost xf-product-cost'})
                    if cost_div==None:
                        continue
                    sale_div = cost_div.find('div', {'class': 'xf-price xf-product-cost__prev'})

                    if sale_div:

                        posted_price_div = cost_div.find('div',{'class':'xf-price xf-product-cost__current js-product__cost _highlight'})
                        price_dict['price_new'] = int(posted_price_div.find('span', {'class': 'xf-price__rouble'}).text)
                        pennies_cost_div = posted_price_div.find('span', {'class': 'xf-price__penny'})
                        if pennies_cost_div is not None:
                            pennies_cost = float(pennies_cost_div.text.strip().replace(',', '.', 1))
                        else:
                            pennies_cost = 0.0

                        price_dict['price_old'] = tofloat(sale_div.text)
                    else:
                        price_dict['price_new'] = int(cost_div.find('span', {'class': 'xf-price__rouble'}).text)
                        pennies_cost_div = cost_div.find('span', {'class': 'xf-price__penny'})
                        if pennies_cost_div is not None:
                            pennies_cost = float(pennies_cost_div.text.strip().replace(',', '.', 1))
                        else:
                            pennies_cost = 0.0
                        price_dict['price_old'] = ''

                    site_unit_div = cost_div.find('span', {'class': 'xf-price__unit'})

                    if site_unit_div is not None:
                        site_unit = site_unit_div.text.split(r'/')[-1].split()[0]
                    else:
                        site_unit = 'шт'
                    price_dict['price_new'] += pennies_cost
                    price_dict['site_unit'] = site_unit
                    price_dict['site_link'] = aref.get('href')
                    price_dict['type'] = 'food'
                    '''
                    print('site_title: {}\nprice_new: {}\nprice_old: {}\n\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old']))
                    '''

                    res = res.append(price_dict, ignore_index=True)


                    # print('   length of res:{}'.format(len(res)))

            # print('\t\tparsed {} items'.format(len(res)- n_items_before))


        end_time = datetime.now().minute
        time_execution = str(timedelta(minutes=end_time - start_time))
        print('PEREKRESTOK has successfully parsed\ntotal time of execution: {}'.format(time_execution))
        if fail_array!=[]:
            print('FAIL URLS:')
            for elem in fail_array:
                print(elem)
        return res

    def extract_product_page(self):
        site_code = 'vprok'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        # ua = UserAgent()
        # header = {'User-Agent': str(ua.chrome)}

        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        # proxies = get_proxy('https://www.vprok.ru/')  #  #
        proxies = None

        # selenium

        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):
                clever_sleep()
                href_i = url_list[i]

                print(href_i)

                HEADERS = {'Accept': '*/*',
                           'Connection': 'keep-alive',
                           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
                           'Accept-Encoding': 'gzip, deflate, br',
                           'Accept-Language': 'en-US;q=0.5,en;q=0.3', 'Cache-Control': 'max-age=0',
                           'DNT': '1', 'Upgrade-Insecure-Requests': '1', 'Referer': 'https://google.com'}

                TIMEOUT = 60

                i += 1


                try:
                    if proxies != None:
                        r = requests.get(href_i, proxies=proxies, headers=HEADERS, timeout=TIMEOUT)  # CRITICAL
                    else:
                        r = requests.get(href_i, headers=HEADERS, timeout=TIMEOUT)
                    if 'Если считаете, что произошла ошибка' in r.text:
                        raise ValueError('Нас забанили!')
                except Exception as e:
                    print(e)
                    while True:
                        try:
                            proxies = get_proxy(href_i)
                            r = requests.get(href_i, proxies=proxies, headers=HEADERS, timeout=TIMEOUT)
                            time.sleep(3)
                            if r.status_code == 200 and 'Если считаете, что произошла ошибка' not in r.text:
                                break
                        except:
                            continue
                if 'Выполняется' in r.text:
                    clever_sleep(mu=3)
                html = r.content
                soup = BeautifulSoup(html, 'lxml')

                if 'страница не существует' in soup:
                    continue
                price_dict = dict()
                # print(soup)
                # print('city:', soup.find('span', {'class': 'js-address-data'}).text)
                try:
                    price_dict['site_title'] = wspex_space(
                        soup.find('h1', {'class': re.compile('Title_title__nvodu')}).text)
                except:
                    # print(soup)
                    print('site_title not found!')
                    continue

                print('site_title:', price_dict['site_title'])
                if 'Распродано' in soup.text:
                    print('Распродано!')
                    continue

                if 'Временно недоступен' in soup.text or 'Временно отсутствует' in soup.text:
                    print('Временно отсутствует!')
                    continue

                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title
                price_div = soup.find('div', {'class': 'PriceInfo_root__GX9Xp'})
                if not price_div:
                    print('im here')
                    price_div = soup.find('div', {'class': 'BuyQuant_price__7f54F'})
                div_sale = price_div.find('span', {'class': 'Price_role_old__r1uT1'})
                if div_sale is not None:
                    # print('div-sale:', div_sale)
                    price_dict['price_old'] = float(re.search('\d+\.*\d+', wspex(div_sale.text).replace(',', '.'))[0])
                    if price_dict['price_old'] == 0.0:
                        price_dict['price_old'] = ''
                else:
                    price_dict['price_old'] = ''

                div_new = price_div.find('span',
                                        {'class': 'Price_price__QzA8L Price_size_XL__MHvC1 Price_role_discount__l_tpE'})
                if div_new is None:
                    div_new = price_div.find('span', {
                        'class': re.compile('Price_price__QzA8L Price_size_XL__MHvC1 Price_role_regular__X6X4D\s*')})

                if div_new is None:
                    print('\tdiv_new is None!')
                    # print('products_div:', products_div)
                    continue
                price_dict['price_new'] = float(re.search('\d+\.*\d+', wspex(div_new.text).replace(',', '.'))[0])
                if type(price_dict['price_old']) is float:
                    if price_dict['price_old'] < price_dict['price_new']:
                        print('Old price is less than new one!')
                        price_dict['price_old'] = ''
                piece_units = ['шт', 'штук', 'штуки', 'штука', 'пак', 'пакетиков', 'пак']
                kg_units = ['кг', 'kg', 'килограмм']  # оставить в граммах
                gram_units = ['г', 'g', 'грамм', 'граммов', 'гр']  # в кг
                litre_units = ['л', 'l', 'литр', 'литров', 'литра']
                ml_units = ['мл', 'ml', 'миллилитров', 'миллилитра']
                tenpiece_units = ['10 шт', '10 шт.', '10шт', '10шт.', 'десяток', 'дес.']

                kg_pattern = r'\s+(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(kg_units) + r')' + '(?:\s+|$)'
                g_pattern = r'\s+(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(gram_units) + r')' + '(?:\s+|$)'
                l_pattern = r'\s+(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(litre_units) + r')' + '(?:\s+|$)'
                ml_pattern = r'\s+(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(ml_units) + r')' + '(?:\s+|$)'
                piece_pattern = r'\s+(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                    piece_units) + r')' + '(?:\s+|$)'
                tenpiece_pattern = r'\s*(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                    tenpiece_units) + r')' + '(?:\s+|$)'

                patterns = [piece_pattern, tenpiece_pattern, kg_pattern, g_pattern, l_pattern, ml_pattern]
                price_dict['site_unit'] = None
                for pattern in patterns:
                    match = re.search(pattern, price_dict['site_title'].lower())
                    if match:
                        price_dict['site_unit'] = wspex_space(match[0])
                        # print(price_dict['site_unit'])

                if price_dict['site_unit'] is None:
                    price_dict['site_unit'] = 'шт.'

                price_dict['site_link'] = href_i  # показывает название товара и ссылку на него
                price_dict['type'] = 'food'
                print('price_new: {}\nprice_old: {}\nunit: {}\n'.format(
                                                                        price_dict['price_new'],
                                                                        price_dict['price_old'],
                                                                        price_dict['site_unit']))
                res = res.append(price_dict, ignore_index=True)

        print('PEREKRESTOK has successfully parsed')
        return res