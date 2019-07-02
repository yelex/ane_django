from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from datetime import datetime
from fake_useragent import UserAgent
from .tools import list_html, wspex_space, find_float_number, filter_flag, wspex, get_proxy
from .global_status import Global
from tqdm import tqdm

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

        path_sfb = r'description\urls.csv'
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
        site_code = 'utkonos'
        ua = UserAgent()
        # header = {'User-Agent': str(ua.chrome)}
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)].iloc[:Global().max_links]

        links_df = links_df

        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])
        proxies = None
        # proxies = get_proxy('https://www.utkonos.ru/')
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):

                href_i = url_list[i]
                i += 1

                print('href_i: ', href_i)

                if proxies is not None:
                    r = requests.get(href_i, proxies=proxies)
                else:
                    r = requests.get(href_i)
                html = r.content

                soup = BeautifulSoup(html, 'html.parser')
                # print('soup:\n', soup)
                products_div = soup.find('div', {'class': 'goods_view_item-action'})
                # print('products_div:\n', products_div)
                price_dict = dict()

                price_dict['date'] = Global().date
                price_dict['site_code'] = 'utkonos'
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title

                price_dict['site_title'] = wspex_space(
                    products_div.find('div', {'class': 'goods_view_item-action_header'}).text)
                price_dict['site_link'] = href_i
                # print(price_dict['site_link'])

                # if filter_flag(id_n, price_dict['site_title']) == False:
                # print("   skipped position: {}".format(price_dict['site_title']))
                # continue
                price_div = products_div.find('div', {'class': 'goods_price has_old_price'})

                # print('div_sale:', div_sale)
                if price_div is not None:

                    div_sale = price_div.find('div', {'class': 'goods_price-item old_price'})
                    # print('div_sale: ', div_sale)
                    price_dict['price_old'] = float(re.search('\d+\.\d+', wspex(div_sale.text).replace(',', '.'))[0])

                    div_new = price_div.find('div', {'class': 'goods_price-item current'})
                    if div_new is None:
                        div_new = price_div.find('div', {'class': 'goods_price-item current big'})
                    price_dict['price_new'] = float(re.search('\d+\.\d+', wspex(div_new.text).replace(',', '.'))[0])

                    price_dict['site_unit'] = str(div_new.get('data-weight'))[1:]

                else:
                    div_new = products_div.find('div', {'class': 'goods_price-item current'})
                    if div_new is None:
                        div_new = products_div.find('div', {'class': 'goods_price-item current big'})
                    price_dict['price_new'] = float(re.search('\d+\.\d+', wspex(div_new.text).replace(',', '.'))[0])
                    price_dict['price_old'] = ''
                    price_dict['site_unit'] = str(div_new.get('data-weight'))[1:]
                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old'],
                                                                                        price_dict['site_unit']))
                # print(price_dict)
                price_dict['type'] = 'food'
                res = res.append(price_dict, ignore_index=True)

        print('UTKONOS has successfully parsed')
        return res
