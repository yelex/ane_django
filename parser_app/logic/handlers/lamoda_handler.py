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
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

class LamodaHandler:

    # def extract_products(self, max_prod=200):
    #
    #     # proxies = get_proxy('https://www.lamoda.ru/')
    #     ua = UserAgent()
    #     header = {'User-Agent': str(ua.chrome)}
    #     # количество страниц
    #     path_sfb = os.path.join(Global.base_dir, r'description/urls.csv')
    #     sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
    #
    #     list_urls = sfb_df[sfb_df.fillna('')['URL'].str.contains('lamoda')]['URL'].values  # ссылки на URL lamoda
    #
    #     res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
    #                        'site_title', 'price_new', 'price_old', 'site_unit',
    #                        'site_link', 'site_code'])
    #
    #     start_html = 'https://www.lamoda.ru'
    #     id_n = -1
    #     fail_list=[]
    #
    #     store = 'lamoda'
    #
    #     for url in tqdm(list_urls):
    #
    #         id_n += 1
    #         category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('lamoda')]['cat_title'].iloc[id_n]
    #
    #         print('\n{} ...'.format(category_title))
    #         page = 0
    #
    #         cat_row = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
    #                        'site_title', 'price_new', 'price_old', 'site_unit',
    #                        'site_link', 'site_code'])
    #
    #         try:
    #             # time.sleep(3)
    #             r = requests.get(url, headers=header)
    #         except:
    #             print('need proxy!')
    #             proxies = get_proxy(url)
    #             r = requests.get(url, proxies=proxies, headers=header)
    #         html = r.content
    #
    #         soup = BeautifulSoup(html, 'lxml')
    #         if soup.find('span', {'class': 'products-catalog__head-counter'})!=None:
    #             total_amount = int(
    #                 re.search('\d+', wspex(soup.find('span', {'class': 'products-catalog__head-counter'}).text)).group())
    #             # print('total_amount: ', total_amount)
    #         else:
    #             print('total_amount HAS NOT BEEN FOUND! ', total_amount)
    #             fail_list.append(id_n)
    #             continue
    #
    #         while True:
    #             # time.sleep(2)
    #             page += 1
    #             url_i = url + '?page={}'.format(page)
    #             print('   loading url:{}'.format(url_i))
    #             try:
    #                 r = requests.get(url_i, proxies=proxies)
    #             except:
    #                 proxies = get_proxy(url)
    #                 r = requests.get(url_i, proxies=proxies)
    #             html = r.content
    #
    #             soup = BeautifulSoup(html, 'lxml')
    #
    #             product_div = soup.findAll('a', {'class': 'products-list-item__link link'})
    #             for product in product_div:
    #                 product_dict = dict()
    #                 product_dict['category_id'] = int(sfb_df.fillna('')[sfb_df.fillna('')['URL'].str.contains('lamoda')].index[id_n])
    #                 # print('category_id: ', product_dict['category_id'])
    #                 product_dict['date'] = Global().date
    #                 product_dict['site_code'] = store
    #                 product_dict['category_title'] = category_title
    #                 product_dict['site_title'] = wspex_space(
    #                     product.find('img').attrs['alt'])  # find('div', {'class': 'products-list-item__brand'}).text)
    #                 product_dict['site_link'] = start_html + product.attrs['href']
    #                 product_dict['site_unit'] = 'шт.'
    #                 cost_text = product.find('span', {'class': 'price'})
    #                 #print(cost_text)
    #                 try:
    #                     product_dict['price_new'] = tofloat(wspex(cost_text.find('span', {'class': 'price__new'}).text))
    #
    #                     product_dict['price_old'] = tofloat(
    #                         wspex(cost_text.find('span', {'class': 'price__old'}).text))
    #                     product_dict['price_new'] = int(product_dict['price_new'])
    #                     product_dict['price_old'] = int(product_dict['price_old'])
    #
    #                 except:
    #                     product_dict['price_new'] = tofloat(wspex(cost_text.find('span', {'class': 'price__actual'}).text))
    #                     product_dict['price_old'] = ''
    #                     product_dict['price_new'] = int(product_dict['price_new'])
    #
    #                 product_dict['type'] = 'non-food'
    #
    #                 if product_dict['price_new']=='' or  product_dict['price_new'] == None:
    #                     print('{} has no price!!!'.format(product_dict['site_title']))
    #
    #                     #print('title: {}\nprice_new: {}\nprice_old: {}\n\n'.format(product_dict['site_title'],product_dict['price_new'],product_dict['price_old']))
    #                 cat_row = cat_row.append(product_dict, ignore_index=True)
    #                 #print(cat_row[['site_title','price_new','price_old']])
    #
    #             if len(cat_row) >= max_prod or len(cat_row) == total_amount:
    #                 res = res.append(cat_row, ignore_index=True)
    #                 break
    #             else:
    #                 continue
    #
    #     if fail_list != []:
    #         for elem in fail_list:
    #             print('CATEGORY {} HAS NOT BEEN PARSED'.format(elem))
    #
    #     return res

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

            # ua = UserAgent(verify_ssl=False)
            header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
            while i + 1 <= len(url_list):

                href_i = url_list[i]
                print(href_i)
                i += 1

                try:
                    time.sleep(3)
                    if proxies is not None:
                        r = requests.get(href_i, proxies=proxies, headers=header, timeout=100)  # CRITICAL
                    else:
                        r = requests.get(href_i, headers=header, timeout=100)
                except:
                    while True:

                        proxies = get_proxy(href_i)
                        time.sleep(3)
                        try:
                            r = requests.get(href_i, proxies=proxies, headers=header)
                            soup = BeautifulSoup(r.content, 'lxml')
                            if 'not found' in soup.text.lower():
                                print('not found')
                                break
                            if r.status_code == 200:
                                break
                        except Exception as e:
                            print(e)
                            continue

                html = r.content

                soup = BeautifulSoup(html, 'lxml')
                # print(soup)
                products_div = soup.find('div', {'class': 'ii-product__aside-wrapper'})
                try:
                    soup.find('div', {'class': 'ii-product__buy js-widget-buy ii-product__buy_disabled'}).get('data-dict-out_of_stock')
                    print('Товара нет в наличии')
                    continue
                except:
                    # print(soup)
                    pass

                if 'not found' in soup.text.lower():
                    print('not found')
                    continue
                if 'Мы не смогли найти страницу по вашей ссылке' in soup.text:
                    print('Мы не смогли найти страницу по вашей ссылке')
                    continue
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

                type_good = wspex_space(soup.find('div', {'class': 'ii-product'}).get('data-name'))

                if type_good == '':
                    # print(' imhere!')
                    raise AttributeError
                    # type_good = wspex_space(text_diff(soup.find('span', {'class': 'heading_m ii-product__title'}).text,
                    #                                   soup.find('span', {'class': 'ii-product__brand'}).text))

                try:

                    price_dict['site_title'] = type_good + ' Артикул: ' + wspex_space(
                        soup.find('div', {'class': 'ii-product'}).get('data-sku'))

                except:
                    continue
                # print(products_div)
                # print(str(soup))
                div_prices = soup.find('div', {'class': 'product-prices'})
                # print(div_prices)
                if len(div_prices.findAll('span')) == 2:
                    # print('there is discount')
                    div_old = div_prices.findAll('span')[0]
                    div_new = div_prices.findAll('span')[1]
                    # print(f'div_new: {div_new}\ndiv_old: {div_old}')
                else:
                    # print('there is no discount')
                    div_old = None
                    div_new = div_prices.findAll('span')[0]
                #

                price_dict['price_new'] = int(re.match('\d+', wspex(div_new.text))[0])
                if div_old:
                    price_dict['price_old'] = int(re.match('\d+', wspex(div_old.text))[0])
                else:
                    price_dict['price_old'] = ''


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