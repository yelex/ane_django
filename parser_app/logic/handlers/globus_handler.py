from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import requests
import re
from parser_app.logic.global_status import Global
import os
from parser_app.logic.handlers.tools import filter_flag, list_html, wspex_space, get_proxy, clever_sleep
from tqdm import tqdm
import time
from fake_useragent import UserAgent
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


class GlobusHandler:

    def construct_html(self,start_html,begin_index):
        end_html='&PAGEN_2={}'.format(begin_index)
        html=start_html+end_html
        return(html)

    def extract_products(self):
        start_time = datetime.now().minute
        path_sfb = os.path.join(Global.base_dir, r'description/urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
        hrefs = sfb_df[sfb_df.fillna('')['URL'].str.contains('globus')]['URL'].values
        id_n = 0
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])
        proxies = get_proxy(hrefs[0])
        header = UserAgent(verify_ssl=False).chrome
        for href in tqdm(hrefs): #испр
            id_n += 1
            category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('globus')]['cat_title'].iloc[id_n - 1]

            print("{}... ".format(category_title))

            #print(' id_n =', id_n)
            url_list = list_html(href)
            i = 0

            while i + 1 <= len(url_list):
                url = url_list[i]

                i += 1
                it_error = 0

                page = 0
                while True:
                    page += 1

                    href_i = self.construct_html(url, page)
                    # print('loading {} ...'.format(href_i))
                    try:
                        clever_sleep()
                        if proxies != None:
                            r = requests.get(href_i, proxies=proxies, headers=header, timeout=10)
                        else:
                            r = requests.get(href_i, headers=header, timeout=10)
                    except:
                        while r.status_code != 200:
                            proxies = get_proxy(href_i)
                            time.sleep(3)
                            r = requests.get(href_i, proxies=proxies, headers=header, timeout=10)
                    html = r.content
                    soup = BeautifulSoup(html, 'lxml')
                    products_div = soup.find('div', {'class': 'catalog-section'})
                    if not products_div:
                        print('WARNING! {} has not product_div'.format(href_i))
                        it_error+=1
                        if it_error>5:
                            break
                        else:
                            continue
                    amount_div = soup.find('div', {'class': 'catalog-content'})
                    total_amount = int('0' + amount_div.find('h1').find('sub').text.split(' ')[0])
                    price_list = products_div.find_all('div', {'class': 'catalog-section__item__body trans'})

                    if page * 64 >= total_amount:
                        flag_nextpage = False
                    else:
                        flag_nextpage = True

                    for price_elem in price_list:
                        price_dict = dict()
                        price_dict['date'] = Global().date
                        price_dict['site_code'] = 'globus'
                        price_dict['category_id'] = id_n
                        price_dict['category_title'] = sfb_df[sfb_df.fillna('')['URL'].str.contains('globus')]['cat_title'].iloc[id_n-1]
                        price_dict['type'] = 'food'
                        price_dict['site_title'] = price_elem.find('span', {'class': 'catalog-section__item__title'}).text

                        # print('category_title: {}\nsite_title: {}'.format(price_dict['category_title'],price_dict['site_title']))
                        if filter_flag(id_n, price_dict['site_title']) == False:
                            # print("skipped position: {}".format(price_dict['site_title']))
                            continue

                        price_text_rub_div = price_elem.find('span', {'class': 'item-price__rub'})
                        price_text_kop_div = price_elem.find('span', {'class': 'item-price__kop'})
                        price_text_old_div = price_elem.find('span', {'class': 'item-price__old'})

                        if not price_text_rub_div or not price_text_kop_div:
                            continue

                        try:
                            price_dict['price_new'] = int(price_text_rub_div.text.replace(" ", ""))+\
                                                      0.01 * int(price_text_kop_div.text)
                        except:
                            price_dict['price_new'] = int(price_text_rub_div.text.replace("\xa0", "")) + \
                                                      0.01 * int(price_text_kop_div.text)

                        if price_text_old_div:
                            list_ = re.findall('\s+', wspex_space(price_text_old_div.text))

                            if len(list_) == 2:
                                price_text = re.sub('\s+', '', wspex_space(price_text_old_div.text), count=1)
                                price_text = re.sub('\s+', '.', price_text)

                            else:
                                price_text = re.sub('\s+', '.', wspex_space(price_text_old_div.text))
   
                            price_dict['price_old'] = float(price_text)
                        else:
                            price_dict['price_old'] = ''

                        price_dict['site_unit'] = price_elem.find('span', {'class':
                                                                               'item-price__additional item-price__additional--solo'}).text.strip()
                        price_dict['site_link'] = price_elem.find('a', {'class':
                                                                            'catalog-section__item__link catalog-section__item__link--one-line notrans'}).get(
                            'href')
                        res = res.append(price_dict, ignore_index=True)

                    if flag_nextpage == False:
                        break
                    else:
                        continue

        end_time = datetime.now().minute
        time_execution = str(timedelta(minutes=end_time - start_time))
        print('GLOBUS has successfully parsed\ntotal time of execution: {}'.format(time_execution))
        return (res)

    def extract_product_page(self):
        site_code = 'globus'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        # ua = UserAgent(verify_ssl=False, use_cache_server=False)
        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])
        url = 'https://online.globus.ru/'
        while True:
            try:
                # proxies = get_proxy(url)
                # time.sleep(3)
                r = requests.get(url, headers=header)
                soup = BeautifulSoup(r.content, 'lxml')
                # print(BeautifulSoup(r.content))

                if soup.find('body', {'id': 'globus-app'}) is not None:
                    break
            except Exception as e:
                print('Exception:', e)
                continue

        # proxies = get_proxy('https://online.globus.ru/')
        proxies = None

        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):
                url = url_list[i]

                i += 1

                print('{} ...'.format(url))
                try:
                    time.sleep(2)
                    if proxies is not None:
                        r = requests.get(url, proxies=proxies, headers=header, timeout=10)  # CRITICAL
                    else:
                        r = requests.get(url, headers=header, timeout=10)
                except Exception as e:
                    print(e)
                    if 'timeout' in str(e):
                        continue
                    while True:
                        try:
                            proxies = get_proxy(url)
                            time.sleep(3)
                            r = requests.get(url, proxies=proxies, headers=header)
                            soup = BeautifulSoup(r.content)
                            print(BeautifulSoup(r.content))

                            if soup.find('body', {'id': 'globus-app'}) is not None:
                                break
                        except Exception as e:
                            print('Exception:', e)
                            continue
                html = r.content
                soup = BeautifulSoup(html, 'lxml')
                if 'Неправильно набран адрес' in soup.text:
                    print('Error 404')
                    continue
                products_div = soup.find('div', {'class': 'item-card__content--right'})

                price_dict = dict()
                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title
                price_dict['type'] = 'food'
                try:
                    price_dict['site_title'] = wspex_space(
                        products_div.find('h1', {'class': 'js-with-nbsp-after-digit'}).text)
                except:
                    print('OOPS! {} has not been parsed'.format(url))
                    continue

                # if filter_flag(id_n, price_dict['site_title']) == False:
                # print("skipped position: {}".format(price_dict['site_title']))
                # continue
                price_div = products_div.find('span', {'class': 'item-price'})

                price_text_rub_div = price_div.find('span', {'class': 'item-price__rub'})
                price_text_kop_div = price_div.find('span', {'class': 'item-price__kop'})
                price_text_old_div = price_div.find('span', {'class': 'item-price__old'})

                if not price_text_rub_div or not price_text_kop_div:
                    continue

                try:
                    price_dict['price_new'] = int(price_text_rub_div.text.replace(" ", "")) + \
                                              0.01 * int(price_text_kop_div.text)
                except:
                    price_dict['price_new'] = int(price_text_rub_div.text.replace("\xa0", "")) + \
                                              0.01 * int(price_text_kop_div.text)

                if price_text_old_div:
                    list_ = re.findall('\s+', wspex_space(price_text_old_div.text))

                    if len(list_) == 2:
                        price_text = re.sub('\s+', '', wspex_space(price_text_old_div.text), count=1)
                        price_text = re.sub('\s+', '.', price_text)

                    else:
                        price_text = re.sub('\s+', '.', wspex_space(price_text_old_div.text))

                    price_dict['price_old'] = float(price_text)

                else:
                    price_dict['price_old'] = ''

                price_dict['site_unit'] = products_div.find('span', {'class':
                                                                         'item-price__unit'}).text.strip()
                price_dict['site_link'] = url
                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old'],
                                                                                        price_dict['site_unit']))

                res = res.append(price_dict, ignore_index=True)

        print('GLOBUS has successfully parsed')
        return res