from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from selenium import webdriver
from datetime import datetime
from fake_useragent import UserAgent
from parser_app.logic.handlers.tools import list_html, wspex_space, find_float_number, filter_flag, wspex, get_proxy
from parser_app.logic.global_status import Global
from tqdm import tqdm
import time
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

class UtkonosHandler():

    def representsInt(self,s):
        try:
            intnumber = int(s)
            return intnumber
        except ValueError:
            return None

    def construct_html(self,start_html, page_number):
        end_html = '/page/{}'.format(page_number)
        html = start_html + end_html
        return (html)

    def extract_products(self):

        start_time = datetime.now()

        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

        path_sfb = r'description/urls.csv'
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')

        hrefs = [href for href in hrefs if type(href) is not float]  # испр
        id_n = 0
        #proxies = get_proxy('https://www.utkonos.ru/')

        for href in tqdm(hrefs):
            #
            id_n += 1
            category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('utkonos')]['cat_title'].iloc[id_n-1]
            print("{}...".format(category_title))

            url_list = list_html(href)
            i = 0

            while i + 1 <= len(url_list):

                href_i = url_list[i]
                i += 1
                page = 0
                while True:
                    page += 1

                    url_full = self.construct_html(href_i, page)

                    print('loading url', url_full)

                    try:
                        r = requests.get(url_full)  # CRITICAL
                    except:
                        raise ValueError
                        #proxies = get_proxy('https://www.utkonos.ru/')
                        #r = requests.get(url_full, proxies=proxies)
                    html = r.content

                    soup = BeautifulSoup(html, 'lxml')

                    try:
                        products_div = soup.find('div', {'class': 'goods_view_box'})

                    except:
                        print("OOPS! {} has no products_div".format(url_full))
                        continue

                    pages_controller_div = soup.find('div', {'class': 'el_paginate'})
                    if pages_controller_div is None:
                        # print('no_pages_controller')
                        flag_nextpage = False
                    else:
                        pages_refs = pages_controller_div.find_all('a')
                        max_page_index = 1

                        for ref in pages_refs:
                            page_index = self.representsInt(ref.text.strip())
                            if page_index is not None:
                                if page_index > max_page_index:
                                    max_page_index = page_index
                        if max_page_index > page:
                            # print('max_page_index: ', max_page_index)
                            flag_nextpage = True
                            # print('nextpage!')
                        else:
                            flag_nextpage = False
                            # print('nonextpage!')

                    try:
                        price_list = products_div.find_all('div', {'class': 'goods_view_box-view goods_view goods_view-item'})
                    except:
                        print("OOPS! {} has no price_list".format(url_full))
                        continue

                    for price_elem in price_list:

                        price_dict = dict()

                        price_dict['date'] = Global().date
                        price_dict['site_code'] = 'utkonos'
                        price_dict['category_id'] = id_n
                        price_dict['category_title'] = category_title

                        # product_unavailable_div = price_elem.find('div', {'class': 'product-unavailable-text'})
                        #     if product_unavailable_div is not None:
                        #         continue # just skip
                        #

                        product_name_div = price_elem.find('div', {'class': 'goods_view_box-caption'})
                        if product_name_div is not None:
                            aref = product_name_div.find('a')
                            if aref is not None:
                                price_dict['site_title'] = wspex_space(aref.text)
                                price_dict['site_link'] = aref.get('href')
                            else:
                                continue
                        else:
                            continue
                        if filter_flag(id_n, price_dict['site_title']) == False:
                            # print("   skipped position: {}".format(price_dict['site_title']))
                            continue

                        try:
                            product_price_div = price_elem.find('div', {'class': 'goods_price-item current big'})
                            div_sale = price_elem.find('div', {'class': 'goods_price-item old_price'})
                            if div_sale:
                                price_dict['price_old'] = find_float_number(div_sale.text)
                            else:
                                price_dict['price_old'] = ''


                            # if product_price_div is not None:
                            price_dict['price_new'] = find_float_number(product_price_div.text)

                            if price_dict['price_old'] == price_dict['price_new']:
                                price_dict['price_old'] = ''

                            price_dict['site_unit'] = str(product_price_div.get('data-weight'))[1:]
                        except:
                            product_price_div = price_elem.find('div', {'class': 'goods_price-item current'})

                            # if product_price_div is not None:
                            price_dict['price_new'] = find_float_number(product_price_div.text)
                            price_dict['price_old'] = ''
                            price_dict['site_unit'] = str(product_price_div.get('data-weight'))[1:]
                        """print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                           price_dict['price_new'],
                                                                           price_dict['price_old'],
                                                                           price_dict['site_unit']))"""
                        # print(price_dict)
                        price_dict['type'] = 'food'
                        res = res.append(price_dict, ignore_index=True)

                    if flag_nextpage == False:
                        break
        end_time = datetime.now()
        time_execution = str(end_time-start_time)
        print('UTKONOS has successfully parsed\ntotal time of execution: {}'.format(time_execution))
        return res

    def extract_product_page(self):
        global driver
        site_code = 'utkonos'
        # ua = UserAgent()
        # header = {'User-Agent': str(ua.chrome)}
        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'Utk_DvcGuid=EBD84CCB48685E87A8797114CD8E5641; Utk_SssTkn=C5D643998F7E8EAAE32548B2C36D686A; Utk_LncTime=2021-07-08+19%3A51%3A25; store_mod=full; low_vision=false; store=utk; SGM_210527_1000=178; Utk_MrkGrpTkn=32272049DCF9DBF4A5CD3D9CC0E2FA26; _gcl_au=1.1.519209760.1625763097; _ym_debug=1; gtm_source=na; gtm_medium=referrer; _ga=GA1.2.2081761378.1625763097; _gid=GA1.2.1934410785.1625763097; SGM_VAR=A; tmr_lvid=8d36ea6d24fda949e1be9751a412fbc8; tmr_lvidTS=1625763132329; _fbp=fb.1.1625763132904.762725467; _tm_lt_sid=1625763132357.432652; _ym_uid=1625763134605670190; _ym_d=1625763134; uid=6818944816957620224; _ym_isad=2; tmr_detect=0%7C1625763134711; flocktory-uuid=01abba0d-5099-47f0-bdab-053080ec689d-0; ADRUM=s=1625763781150&r=https%3A%2F%2Fwww.utkonos.ru%2Fitem%2F3399082%2Fmoloko-super-ultrapasterizovannoe-3-2-1-l%3F0; tmr_reqNum=4',
            'Host': 'www.utkonos.ru',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36}'}
        # print(header)
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]

        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])
        check_url = links_df[links_df.category_id == 1].site_link.values[0]
        # proxies = get_proxy(check_url) #
        proxies = None

        # selenium
        if Global().is_selenium_utkonos:
            path = Global().path_chromedriver
            # options = webdriver.ChromeOptions()
            # options.add_argument('--headless')

            driver = webdriver.Chrome(executable_path=path, chrome_options=Global().chrome_options)

        #
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):

                href_i = url_list[i]
                i += 1

                print(href_i)
                if Global().is_selenium_utkonos:
                    try:
                        driver.get(href_i)
                    except:
                        driver.get(href_i)
                    time.sleep(5)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    # driver.close()
                else:
                    # time.sleep(3)
                    try:
                        if proxies is not None:
                            r = requests.get(href_i, proxies=proxies, headers=header)
                        else:
                            r = requests.get(href_i, headers=header)
                    except Exception as e:
                        print('Exception:', e)
                        while True:
                            try:
                                proxies = get_proxy(href_i)
                                time.sleep(3)
                                r = requests.get(href_i, proxies=proxies, headers=header)
                                break
                            except:
                                continue

                    html = r.content

                    soup = BeautifulSoup(html, 'html.parser')
                #                 print('soup:\n', soup)
                if 'Упс! Страница не найдена' in soup.text:
                    print('Упс! Страница не найдена')
                    continue
                products_div = soup.find('div', {'class': 'product-base-info_content'})
                # print('soup:\n', soup)
                if products_div is None:
                    print('products_div is None!')
                    continue
                    # print(soup)
                    # while True:
                    #     proxies = get_proxy(href_i)
                    #     time.sleep(3)
                    #     r = requests.get(href_i, proxies=proxies, headers=header)
                    #     html = r.content
                    #     soup = BeautifulSoup(html, 'html.parser')
                    #     # print(soup)
                    #     if soup.find('h1', {'class': 'product-base-info_name ng-star-inserted'}) is not None:
                    #         print('yahoo!')
                    #         break

                price_dict = dict()

                price_dict['date'] = Global().date
                price_dict['site_code'] = 'utkonos'
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title

                try:
                    price_dict['site_title'] = wspex_space(
                        soup.find('h1', {'class': 'product-base-info_name title-l2 ng-star-inserted'}).text)
                except Exception as e:
                    print(e)
                    print('soup:\n', soup)
                    # raise AttributeError
                    continue
                if 'InStock' not in soup.find('meta', {"itemprop": "availability"}).get('content'):
                    print('Снят с продажи!\n')
                    continue

                price_dict['site_link'] = href_i

                price_div = soup.find('div', {'class': 'product-price-block'})
                if price_div is None:
                    raise AttributeError('price_div is none')

                # print('div_sale:', div_sale)

                div_sale = price_div.find('span',
                                          {'class': 'product-old-price--strike'})  # print('div_sale: ', div_sale)

                if div_sale:
                    price_dict['price_old'] = float(re.search('\d+\.\d+', wspex(div_sale.text).replace(',', '.'))[0])
                else:
                    price_dict['price_old'] = ''

                price_dict['site_unit'] = None
                price_dict['price_new'] = None
                # если есть цена за кг
                if price_div.find('span', {'class': 'product-price title-l6 ng-star-inserted'}) is not None:
                    price_dict['price_new'] = float(re.search('\d+\.\d+', wspex(
                        price_div.find('span', {'class': 'product-price title-l6 ng-star-inserted'}).text).replace(',',
                                                                                                                   '.'))[
                                                        0])
                    price_dict['site_unit'] = re.search('/[а-яА-Я]*', price_div.find('span', {
                        'class': 'product-price title-l6 ng-star-inserted'}).text.lower())[0][1:]
                else:
                    if price_div.find('span', {'class': 'product-price ng-star-inserted'}) is not None:
                        price_dict['price_new'] = float(re.search('\d+\.\d+', wspex(
                            price_div.find('span', {'class': 'product-price ng-star-inserted'}).text).replace(',',
                                                                                                              '.'))[0])
                        price_dict['site_unit'] = re.search('/[а-яА-Я]*', price_div.find('span', {
                            'class': 'product-price ng-star-inserted'}).text.lower())[0][1:]
                    # если нет
                    else:
                        if price_div.find('span',
                                          {'class': 'product-sale-price title-l1 __accent ng-star-inserted'}) is not None:
                            price_dict['price_new'] = float(re.search('\d+\.\d+', wspex(price_div.find('span', {
                                'class': 'product-sale-price title-l1 __accent ng-star-inserted'}).text).replace(',', '.'))[0])
                        else:

                            if price_div.find('span', {'class': 'product-sale-price title-l1 ng-star-inserted'}) is not None:
                                price_dict['price_new'] = float(re.search('\d+\.\d+', wspex(price_div.find('span', {
                                    'class': 'product-sale-price title-l1 ng-star-inserted'}).text).replace(',', '.'))[0])

                if price_dict['site_unit'] is None:
                    piece_units = ['шт', 'штук', 'штуки', 'штука', 'пак', 'пакетиков', 'пак']
                    kg_units = ['кг', 'kg', 'килограмм']  # оставить в граммах
                    gram_units = ['г', 'g', 'грамм', 'граммов', 'гр']  # в кг
                    litre_units = ['л', 'l', 'литр', 'литров', 'литра']
                    ml_units = ['мл', 'ml', 'миллилитров', 'миллилитра']
                    tenpiece_units = ['10 шт', '10 шт.', '10шт', '10шт.', 'десяток', 'дес.']

                    kg_pattern = r'(?:\s+|\-)(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                        kg_units) + r')' + '(?:\s+|$)'
                    g_pattern = r'(?:\s+|\-)(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                        gram_units) + r')' + '(?:\s+|$)'
                    l_pattern = r'(?:\s+|\-)(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                        litre_units) + r')' + '(?:\s+|$)'
                    ml_pattern = r'(?:\s+|\-)(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                        ml_units) + r')' + '(?:\s+|$)'
                    piece_pattern = r'(?:\s+|\-)(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                        piece_units) + r')' + '(?:\s+|$)'
                    tenpiece_pattern = r'(?:\s*|\-)(?:\d{1,4}[×,.]\d{1,4}|\d{0,4})\s*(?:' + r'|'.join(
                        tenpiece_units) + r')' + '(?:\s+|$)'

                    patterns = [piece_pattern, tenpiece_pattern, kg_pattern, g_pattern, l_pattern, ml_pattern]

                    for pattern in patterns:
                        match = re.search(pattern, price_dict['site_title'].lower())
                        if match:
                            price_dict['site_unit'] = wspex_space(match[0])
                            if price_dict['site_unit'].startswith('-'):
                                price_dict['site_unit'] = price_dict['site_unit'][1:]

                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old'],
                                                                                        price_dict['site_unit']))
                # print(price_dict)
                price_dict['type'] = 'food'
                res = res.append(price_dict, ignore_index=True)

        if Global().is_selenium_utkonos:
            driver.quit()

        print('UTKONOS has successfully parsed')
        return res
