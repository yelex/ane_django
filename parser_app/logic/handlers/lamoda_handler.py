from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from tqdm import tqdm
from parser_app.logic.handlers.tools import get_proxy, wspex, wspex_space, tofloat, text_diff
from fake_useragent import UserAgent
from parser_app.logic.global_status import Global
import demjson
import os
import time


class LamodaHandler():

    def extract_products(self, max_prod=200):

        # proxies = get_proxy('https://www.lamoda.ru/')
        ua = UserAgent()
        header = {'User-Agent': str(ua.chrome)}
        # количество страниц
        path_sfb = path_sfb = os.path.join(Global.base_dir, r'description\urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')

        list_urls = sfb_df[sfb_df.fillna('')['URL'].str.contains('lamoda')]['URL'].values  # ссылки на URL lamoda

        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

        start_html = 'https://www.lamoda.ru'
        id_n = -1
        fail_list=[]

        store = 'lamoda'

        for url in tqdm(list_urls):

            id_n += 1
            category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('lamoda')]['cat_title'].iloc[id_n]

            print('\n{} ...'.format(category_title))
            page = 0

            cat_row = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

            try:
                # time.sleep(3)
                r = requests.get(url, headers=header)
            except:
                print('need proxy!')
                proxies = get_proxy(url)
                r = requests.get(url, proxies=proxies, headers=header)
            html = r.content

            soup = BeautifulSoup(html, 'lxml')
            if soup.find('span', {'class': 'products-catalog__head-counter'})!=None:
                total_amount = int(
                    re.search('\d+', wspex(soup.find('span', {'class': 'products-catalog__head-counter'}).text)).group())
                # print('total_amount: ', total_amount)
            else:
                print('total_amount HAS NOT BEEN FOUND! ', total_amount)
                fail_list.append(id_n)
                continue

            while True:
                # time.sleep(2)
                page += 1
                url_i = url + '?page={}'.format(page)
                print('   loading url:{}'.format(url_i))
                try:
                    r = requests.get(url_i, proxies=proxies)
                except:
                    proxies = get_proxy(url)
                    r = requests.get(url_i, proxies=proxies)
                html = r.content

                soup = BeautifulSoup(html, 'lxml')

                product_div = soup.findAll('a', {'class': 'products-list-item__link link'})
                for product in product_div:
                    product_dict = dict()
                    product_dict['category_id'] = int(sfb_df.fillna('')[sfb_df.fillna('')['URL'].str.contains('lamoda')].index[id_n])
                    # print('category_id: ', product_dict['category_id'])
                    product_dict['date'] = Global().date
                    product_dict['site_code'] = store
                    product_dict['category_title'] = category_title
                    product_dict['site_title'] = wspex_space(
                        product.find('img').attrs['alt'])  # find('div', {'class': 'products-list-item__brand'}).text)
                    product_dict['site_link'] = start_html + product.attrs['href']
                    product_dict['site_unit'] = 'шт.'
                    cost_text = product.find('span', {'class': 'price'})
                    #print(cost_text)
                    try:
                        product_dict['price_new'] = tofloat(wspex(cost_text.find('span', {'class': 'price__new'}).text))

                        product_dict['price_old'] = tofloat(
                            wspex(cost_text.find('span', {'class': 'price__old'}).text))
                        product_dict['price_new'] = int(product_dict['price_new'])
                        product_dict['price_old'] = int(product_dict['price_old'])

                    except:
                        product_dict['price_new'] = tofloat(wspex(cost_text.find('span', {'class': 'price__actual'}).text))
                        product_dict['price_old'] = ''
                        product_dict['price_new'] = int(product_dict['price_new'])

                    product_dict['type'] = 'non-food'

                    if product_dict['price_new']=='' or  product_dict['price_new'] == None:
                        print('{} has no price!!!'.format(product_dict['site_title']))

                        #print('title: {}\nprice_new: {}\nprice_old: {}\n\n'.format(product_dict['site_title'],product_dict['price_new'],product_dict['price_old']))
                    cat_row = cat_row.append(product_dict, ignore_index=True)
                    #print(cat_row[['site_title','price_new','price_old']])

                if len(cat_row) >= max_prod or len(cat_row) == total_amount:
                    res = res.append(cat_row, ignore_index=True)
                    break
                else:
                    continue

        if fail_list != []:
            for elem in fail_list:
                print('CATEGORY {} HAS NOT BEEN PARSED'.format(elem))

        return res

    def extract_product_page(self):
        site_code = 'lamoda'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        # proxies = get_proxy('https://www.lamoda.ru/')
        proxies = None

        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            ua = UserAgent()
            header = {'User-Agent': str(ua.chrome)}
            while i + 1 <= len(url_list):

                href_i = url_list[i]
                print(href_i)
                i += 1

                try:
                    # time.sleep(3)
                    if proxies is not None:
                        r = requests.get(href_i, proxies=proxies, headers=header, timeout=60)  # CRITICAL
                    else:
                        r = requests.get(href_i, headers=header, timeout=60)
                except:
                    while True:
                        proxies = get_proxy(href_i)
                        time.sleep(3)
                        try:
                            r = requests.get(href_i, proxies=proxies, headers=header)
                            if r.status_code == 200:
                                break
                        except:
                            continue

                html = r.content

                soup = BeautifulSoup(html, 'lxml')

                products_div = soup.find('div', {'class': 'ii-product-buy'})
                if not products_div:
                    proxies = get_proxy('https://www.lamoda.ru/')
                    i -= 1
                    print('no products_div!')
                    continue

                price_dict = dict()
                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title
                # print(soup)
                div_sale = soup.find('div', {'class': 'ii-product__price-discount'})

                if div_sale is not None:
                    # print('div-sale: ',div_sale)
                    price_dict['price_old'] = float(re.match('\d+', wspex(div_sale.text))[0])
                else:
                    price_dict['price_old'] = ''

                type_good = wspex_space(products_div.find('a', {'class': 'hidden'}).text)
                if type_good == '':
                    # print(' imhere!')
                    type_good = wspex_space(text_diff(soup.find('span', {'class': 'heading_m ii-product__title'}).text,
                                                      soup.find('span', {'class': 'ii-product__brand'}).text))

                try:
                    # if products_div.find('a', {'class': 'hidden'}).text is '':
                        # print(soup)
                    price_dict['site_title'] = type_good + ' Артикул: ' + wspex_space(
                        products_div.find('div', {'class': 'ii-select__option'}).get('data-value'))

                except:
                    continue
                # print(products_div)
                div_new = products_div.find('div', {'class': 'ii-product__price ii-product__price_several'})
                if div_new is None:
                    div_new = products_div.find('div', {'class': 'ii-product__price ii-product__price_several DT1717'})
                dct = demjson.decode(div_new.get('data-several-prices'))

                if len(dct['details']) > 1:
                    price_dict['price_old'] = int(dct['details'][0]['value'])
                    price_dict['price_new'] = int(dct['details'][1]['value'])
                else:
                    price_dict['price_new'] = int(dct['details'][0]['value'])
                '''
                else:
                    div_old = 
                    price_dict['price_old'] = int(wspex())
                    price_dict['price_new'] = int(dct['details'][1]['value'])
                '''

                price_dict['site_unit'] = 'шт.'
                price_dict['site_link'] = href_i  # показывает название товара и ссылку на него
                price_dict['type'] = 'non-food'
                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n\n'.format(price_dict['site_title'],
                                                                                          price_dict['price_new'],
                                                                                          price_dict['price_old'],
                                                                                          price_dict['site_unit']))
                res = res.append(price_dict, ignore_index=True)

        print('LAMODA has successfully parsed')
        return res