from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import demjson
from datetime import datetime, timedelta
from parser_app.logic.handlers.tools import filter_flag, wspex_space, tofloat, get_proxy, wspex
from parser_app.logic.global_status import Global
from tqdm import tqdm
from selenium import webdriver
import time
import os

class OkeyHandler:

    def construct_html(self,start_html,begin_index):
        if start_html[-3:]=='-20':
            end_html='#facet:&productBeginIndex:{}&orderBy:&pageView:grid&minPrice:&maxPrice:&pageSize:&'.format(begin_index)
        else:
            end_html='&productBeginIndex:{}&orderBy:&pageView:grid&minPrice:&maxPrice:&pageSize:&'.format(begin_index)
        html=start_html+end_html
        return(html)

    def extract_products(self):
        start_time = datetime.now().minute
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])
        path_sfb = os.path.join(Global.base_dir, r'description/urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
        hrefs = sfb_df[sfb_df.fillna('')['URL'].str.contains('okeydostavka')]['URL'].values
        hrefs = [href for href in hrefs if type(href) is not float]
        id_n = 0
        # proxies = get_proxy('https://www.okeydostavka.ru/')

        for href in tqdm(hrefs):

            page = 0
            max_page_index = 1
            i = 0
            id_n += 1
            category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('okey')]['cat_title'].iloc[id_n - 1]
            print("{}...".format(category_title))
            while True:
                url_full = self.construct_html(href, i)
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

                # print('loading url', url_full)

                try:
                    r = requests.get(url_full, headers=headers)  # CRITICAL
                    time.sleep(3)
                except:
                    r = 404
                    while r.status_code != 200:
                        proxies = get_proxy(url_full)
                        time.sleep(3)
                        r = requests.get(url_full, proxies=proxies, headers=headers)
                html = r.content

                soup = BeautifulSoup(html, 'lxml')

                products_div = soup.find('div', {'class': 'product_listing_container'})
                if not products_div:
                    continue
                pages_controller_div = soup.find('div', {'class': 'pages pageControlMenu'})
                if not pages_controller_div:
                    flag_nextpage = False
                else:
                    pages_refs = pages_controller_div.find_all('a', {'class': 'hoverover'})
                    page += 1
                    for ref in pages_refs:
                        page_index = int(ref.text.strip())
                        if page_index > max_page_index:
                            max_page_index = page_index
                    if max_page_index > page:
                        flag_nextpage = True
                    else:
                        flag_nextpage = False
                price_list = products_div.find_all('div', {'class': 'product ok-theme'})

                i += len(price_list)

                for price_elem in price_list:
                    price_dict = dict()
                    price_dict['date'] = Global().date
                    price_dict['site_code'] = 'okey'
                    price_dict['category_id'] = id_n
                    price_dict['category_title'] = category_title
                    product_unavailable_div = price_elem.find('div', {'class': 'product-unavailable-text'})
                    if product_unavailable_div:
                        continue

                    aref = price_elem.find('a')

                    price_dict['site_title'] = aref.get('title')

                    if filter_flag(id_n, price_dict['site_title']) == False:
                        # print("skipped position: {}".format(price_dict['site_title']))
                        continue

                    product_price_script = price_elem.find('script', {'id': 'productData_'})
                    script_text = product_price_script.text
                    sr = re.search('var\s+product\s*=\s*(?P<dct>.+\});\s*$\s*', script_text, re.MULTILINE)
                    dct_str = sr.group('dct')
                    dct = demjson.decode(dct_str)  # yaml and json fails here
                    price_dict['price_new'] = dct['price']  # показывает цену, название товара и ссылку на него
                    sale_div = price_elem.find('span',{'class':'label small crossed'})
                    if sale_div:
                        list_price = re.search('\d+\,\d+', sale_div.text)
                        price_dict['price_old'] = tofloat(list_price[0])
                    else:
                        price_dict['price_old'] = ''
                    weight_div = price_elem.find('div', {'class': 'product_weight'})
                    if weight_div:
                        price_dict['site_unit'] = wspex_space(weight_div.text)
                    else:
                        quantity_div = price_elem.find('div', {'class': 'quantity_section'})
                        if quantity_div:
                            price_dict['site_unit'] = '1 уп.'
                        else:
                            print('[okey] For product', price_dict['site_title'], ' weight not found!')
                    price_dict['site_link'] = aref.get('href')  # показывает название товара и ссылку на него
                    price_dict['type'] = 'food'
                    res = res.append(price_dict, ignore_index=True)
                if flag_nextpage == False:
                    break

        end_time = datetime.now().minute
        time_execution = str(timedelta(minutes=end_time - start_time))
        print('OKEY has successfully parsed\ntotal time of execution: {}'.format(time_execution))
        return res

    def extract_product_page(self):
        site_code = 'okey'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]

        if Global().is_selenium_okey:
            path = Global().path_chromedriver
            # options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(executable_path=path, chrome_options=Global().chrome_options)

        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])
        # proxies = get_proxy('https://okeydostavka.ru/')
        proxies = None
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))
            n_err = 0
            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):

                href_i = url_list[i]
                print(href_i)
                i += 1
                # if i % 10 == 0 and i != 0:
                    # proxies = get_proxy(href_i)
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
                if Global().is_selenium_okey:
                    driver.get(href_i)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    driver.close()
                else:
                    try:
                        # time.sleep(3)
                        if proxies is not None:
                            r = requests.get(href_i, proxies=proxies, headers=headers, timeout=60)  # CRITICAL
                        else:
                            r = requests.get(href_i, headers=headers, timeout=60)
                    except:
                        while True:
                            try:
                                proxies = get_proxy(href_i)
                                time.sleep(3)
                                r = requests.get(href_i, headers=headers, proxies=proxies, timeout=60)
                                if r.status_code == 200:
                                    break
                            except:
                                continue

                    html = r.content
                    soup = BeautifulSoup(html, 'lxml')
                # print('url: ', href_i)
                # print(soup)
                products_div = soup.find('div', {'class': re.compile('col-8\s+col-lg-7\s+col-md-6\s+'
                                                          'col-sm-12\s+product-information')})  #col4 product-information
                # print(products_div)
                if products_div is None:
                    print('no products_div!')

                    # proxies = get_proxy('https://okeydostavka.ru/')
                    if n_err == 0:
                        n_err += 1
                        i -= 1
                        proxies = get_proxy('https://okeydostavka.ru/')
                    else:
                        n_err = 0

                    continue


                price_dict = dict()
                price_dict['date'] = Global().date
                price_dict['site_code'] = 'okey'
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title


                price_dict['site_title'] = wspex_space(products_div.find('h1', {'class': 'main_header'}).text)
                # print('site_title:{}\nurl:{}\n\n'.format(price_dict['site_title'],href_i))

                # if filter_flag(id_n, price_dict['site_title']) == False:
                # print("skipped position: {}".format(price_dict['site_title']))
                # continue

                if re.search('price\s+label\s+label-red\s*', products_div.text) is not None:
                    print(href_i, 'has sale!')
                try:
                    if products_div.find('span', {'class': re.compile('price\s+label\s+label-red\s*')}) is not None:
                        price_new_div = wspex(products_div.find('span', {'class': re.compile('price\s+label\s+label-red\s*')}).text)
                        sale_div = products_div.find('span', {'class': 'label small crossed'})
                        price_dict['price_new'] = float(re.search('\d+\,\d+', price_new_div)[0].replace(',', '.'))
                        price_dict['price_old'] = float(re.search('\d+\,\d+', sale_div.text)[0].replace(',', '.'))
                    else:
                        price_dict['price_new'] = products_div.find('span', {
                            'class': re.compile('price\s+label\s*')})  # показывает цену, название товара и ссылку на него
                        price_dict['price_new'] = float(
                            re.search('\d+\,\d+', price_dict['price_new'].text)[0].replace(',', '.'))
                        price_dict['price_old'] = ''
                except:
                    continue
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
                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old'],
                                                                                        price_dict['site_unit']))
                res = res.append(price_dict, ignore_index=True)


        print('OKEY has successfully parsed')
        return res