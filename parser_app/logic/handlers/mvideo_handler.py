from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests, re
from datetime import datetime
from fake_useragent import UserAgent
import ssl
import time
ssl._create_default_https_context = ssl._create_unverified_context

from parser_app.logic.global_status import Global
from tqdm import tqdm
from parser_app.logic.handlers.tools import wspex_space, wspex


class MvideoHandler:

    def extract_product_page(self):
        site_code = 'mvideo'
        ua = UserAgent(verify_ssl=False)
        header = {'User-Agent': r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36'}

        desc_df = Global().desc_df
        links_df = Global().links.replace(np.nan, '')
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        # print(links_df.head())
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        # proxies = get_proxy('https://www.utkonos.ru/')
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):
                time.sleep(3)

                href_i = url_list[i]
                i += 1
                page = 0
                print(href_i)

                r = requests.get(href_i, headers=header)
                html = r.content

                soup = BeautifulSoup(html, 'html.parser')
                # print('soup:\n', soup)
                price_dict = dict()

                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = int(cat_id)
                price_dict['category_title'] = category_title

                # print(soup)
                price_dict['site_title'] = wspex_space(
                        soup.find('h1', {'class': 'e-h1 sel-product-title'}).text)

                price_dict['site_link'] = href_i
                # print(price_dict['site_link'])

                # if filter_flag(id_n, price_dict['site_title']) == False:
                # print("   skipped position: {}".format(price_dict['site_title']))
                # continue
                div_price_content = soup.find('div', {'class': 'o-pay__content-trade'})
                if not div_price_content:
                    div_price_content = soup.find('div', {'class': 'o-pay__content'})
                div_sale = div_price_content.find('div', {'class': 'fl-pdp-price__old'})
                # print('div_sale:', div_sale)
                if div_sale is not None and div_sale.text != '':
                    # print('div_sale: ',div_sale)
                    price_dict['price_old'] = float(re.match('\d+', wspex(div_sale.text))[0])
                else:
                    price_dict['price_old'] = ''

                div_new = div_price_content.find('div', {'class': 'fl-pdp-price__current'})
                price_dict['price_new'] = float(re.match('\d+', wspex(div_new.text))[0])

                if price_dict['price_new'] == price_dict['price_old']:
                    print(soup)
                    raise ValueError

                price_dict['site_unit'] = 'шт.'
                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old'],
                                                                                        price_dict['site_unit']))
                # print(price_dict)
                price_dict['type'] = 'non-food'
                res = res.append(price_dict, ignore_index=True)

        print('Mvideo has successfully parsed')
        return res

