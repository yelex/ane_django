from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from parser_app.logic.handlers.tools import filter_flag, get_proxy, tofloat, wspex_space
from parser_app.logic.global_status import Global
from tqdm import tqdm
import re
import time
from fake_useragent import UserAgent
import ssl

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
        hrefs = sfb_df[sfb_df.fillna('')['URL'].str.contains('perekrestok')]['URL'].values
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
        cookie = r'suuid=2612af35-2fa1-464c-9776-a8729ee5cdc1; luuid=2612af35-2fa1-464c-9776-a8729ee5cdc1; split_segment=7; split_segment_amount=10; noHouse=0; appservername=app0; fcf=3; _dy_csc_ses=t; _dy_c_exps=; _gcl_au=1.1.1101498930.1602849311; _dycnst=dg; tmr_lvid=8199eecf75aa278e274aca7b823f79bb; tmr_lvidTS=1602849311544; _ym_uid=1602849312634665940; _ym_d=1602849312; _gid=GA1.2.116608189.1602849312; _dyid=-2882303570935707106; _dyjsession=2924924e01bc000c2c966b01e714bf3b; dy_fs_page=www.vprok.ru%2Fproduct%2Fcherkizovo-cherkiz-sheyka-svin-ohl-vu-pf-kat-b-1kg--303771; _dycst=dk.m.c.ms.; _dy_geo=RU.EU.RU_MOW.RU_MOW_Moscow; _dy_df_geo=Russia..Moscow; _ym_isad=2; _fbp=fb.1.1602849312171.481873387; flocktory-uuid=7fa0fb16-68aa-4d3c-853e-c3ee945b1c33-1; _dyid_server=-2882303570935707106; _dy_c_att_exps=; _dy_ses_load_seq=51541%3A1602850907093; _dyfs=1602850908656; _dy_lu_ses=2924924e01bc000c2c966b01e714bf3b%3A1602850908658; _dy_toffset=-1; _dy_soct=401501.688468.1602849310*464250.838984.1602849311*484922.888305.1602850907*487393.894852.1602850907*496179.916906.1602850907*498939.923749.1602850907*515052.971092.1602850907*366287.608896.1602850907*451565.810320.1602850907*451564.810319.1602850907*464773.921941.1602850908; tmr_detect=0%7C1602850911632; mindboxDeviceUUID=c59980ec-0612-419a-8d13-02580e94b1a0; directCrm-session=%7B%22deviceGuid%22%3A%22c59980ec-0612-419a-8d13-02580e94b1a0%22%7D; tmr_reqNum=1315; XSRF-TOKEN=eyJpdiI6Im16M1EzVWU2djlNa1wvUkF6RTlMNE13PT0iLCJ2YWx1ZSI6InlhRXhSbkI2RURWanpQXC9uTzhzOVZ1WEd0WElEM2VMM3FjYnpRUjR5bUxUMlNMa2JZcDBldDdBakN1TGJjek5WZmE5N1E5cHJcL3FOeE5nQmJpU0crTUE9PSIsIm1hYyI6ImUyOTEzN2ZhMGRhYjVkYTI0YTdjZTM0MzdhMzNmZWY1ZTJlOTM3YmQ1NjA5MjlhMzZhNTU1NGE5OGM0ODQ2ZTkifQ%3D%3D; aid=eyJpdiI6IklBREluTG1PUmNaYkZKUThseFh3RVE9PSIsInZhbHVlIjoiY1E3SHZUMXVYbmxKc0lkZGswWXFBeVwvbEY5Qzc5SEdLUmxPSGQ4SkllR1pONmdHREREaWxcLzVNYW1jM3pkcnRtMmtcLzZKYnY0WlJ6UHRPZ1o3clU3bXc9PSIsIm1hYyI6ImZjYWIwZGY3Mzg1ZGFmODExMjZkY2JlNjgwOTRjMzZiNzY3YzU2ZmIzOGRlMWU5Yzc5YjJiMTc2OGE4YjVjNGUifQ%3D%3D; appservername=app5; _ga=GA1.1.335220323.1602849312; _ga_B122VKXXJE=GS1.1.1602852969.2.0.1602852969.0'


        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):
                # time.sleep(3)
                href_i = url_list[i]

                print(href_i)

                headers = {
                    'User-Agent': r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36',
                }

                i += 1

                try:
                    if proxies != None:
                        r = requests.get(href_i, proxies=proxies, headers=headers, timeout=60)  # CRITICAL
                    else:
                        r = requests.get(href_i, headers=headers, timeout=60)
                except Exception as e:
                    print(e)
                    while True:
                        try:
                            proxies = get_proxy(href_i)
                            r = requests.get(href_i, proxies=proxies, headers=headers, timeout=60)
                            time.sleep(3)
                            if r.status_code == 200:
                                break
                        except:
                            continue

                html = r.content

                soup = BeautifulSoup(html, 'lxml')
                if 'страница не существует' in soup:
                    continue
                price_dict = dict()
                # print(soup)
                # print('city:', soup.find('span', {'class': 'js-address-data'}).text)
                try:
                    price_dict['site_title'] = wspex_space(
                        soup.find('h1', {'class': re.compile('xf-product-new__title js-product__title js-product-new-title')}).text)
                except:
                    # print(soup)
                    print('site_title not found!')
                    continue

                print('site_title:', price_dict['site_title'])
                if 'Распродано' in soup.text:
                    print('Распродано!')
                    continue

                if 'Временно отсутствует' in soup.text:
                    print('Временно отсутствует!')
                    continue

                products_div = soup.find('div', {'class': 'xf-product-new__price-text'})
                if not products_div:
                    print('no products_div!')
                    # print(soup)
                    continue


                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title
                div_sale = products_div.find('span', {'class': 'xf-product-new__crossout-price-text js-product__old-cost'})
                if div_sale is not None:
                    # print('div-sale:', div_sale)
                    price_dict['price_old'] = float(div_sale.get('data-cost'))
                    if price_dict['price_old'] == 0.0:
                        price_dict['price_old'] = ''
                else:
                    price_dict['price_old'] = ''

                div_new = products_div.find('span',
                                            {'class': 'js-product__cost _with_old_price'})
                if div_new is None:
                    div_new = products_div.find('span', {
                        'class': re.compile('js-product__cost\s*')})

                if div_new is None:
                    print('\tdiv_new is None!')
                    # print('products_div:', products_div)
                    continue
                price_dict['price_new'] = float(div_new.get('data-cost'))
                price_dict['site_unit'] = wspex_space(div_new.get('data-type'))
                price_dict['site_link'] = href_i  # показывает название товара и ссылку на него
                price_dict['type'] = 'food'
                print('price_new: {}\nprice_old: {}\nunit: {}\n'.format(
                                                                        price_dict['price_new'],
                                                                        price_dict['price_old'],
                                                                        price_dict['site_unit']))
                res = res.append(price_dict, ignore_index=True)

        print('PEREKRESTOK has successfully parsed')
        return res