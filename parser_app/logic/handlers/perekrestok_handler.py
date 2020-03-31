import os

from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime, timedelta
from parser_app.logic.handlers.tools import filter_flag, get_proxy, tofloat, wspex_space
from parser_app.logic.global_status import Global
from tqdm import tqdm
import re
import time
from fake_useragent import UserAgent


class PerekrestokHandler:

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
        path_sfb = os.path.join(Global.base_dir, 'description', 'urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')
        hrefs = sfb_df[sfb_df.fillna('')['URL'].str.contains('perekrestok')]['URL'].values
        hrefs = [href for href in hrefs if type(href) is not float]
        # print(hrefs)
        id_n = 0

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
        site_code = 'perekrestok'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        ua = UserAgent()
        header = {'User-Agent': str(ua.chrome)}

        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        proxies = None  # get_proxy('https://www.perekrestok.ru/') #

        cookie = r'noHouse=0; _gcl_au=1.1.444475933.1574074757; _ga=GA1.2.762214331.1574074757; _ym_d=1574074757; _ym_uid=1574074757539893444; flocktory-uuid=3da0c784-c6e6-48a1-b5ad-006da3a9393d-1; tracker_ai_user=BWv32|2019-11-18T10:59:21.089Z; cto_lwid=a238aaa4-fac9-42fb-8702-20f8fa785b79; _dy_c_exps=; _dycnst=dg; _dyid=-3805541292711961998; _dy_c_att_exps=; fcf=2; splitVar=test01-B; regionChange=1; luuid=2a83671e-e74e-43bf-9453-1475f62aefda; ins-product-id=484225; insdrSV=18; suuid=96bfa68c-e76a-4623-9bf0-4109601bdb57; _dy_csc_ses=t; _gid=GA1.2.710391697.1575716218; _dyjsession=f58bf955e8baea66ef52b8df2f36e6db; _dy_geo=RU.EU.RU_TUL.RU_TUL_Kireyevsk; _dy_df_geo=Russia..Kireyevsk; _ym_visorc_43992189=w; _ym_isad=1; _dycst=dk.w.c.ss.; _dy_toffset=-3; _dy_ses_load_seq=22331%3A1575717228721; _dy_soct=401501.688467.1575716213*404726.695596.1575716217*405772.698298.1575717228*405837.698434.1575717228*446004.795652.1575717228*366287.608896.1575717228; tmr_detect=1%7C1575717234838; mindboxDeviceUUID=dc46eafc-5856-4f9a-8f46-c7194b0dc0a5; directCrm-session=%7B%22deviceGuid%22%3A%22dc46eafc-5856-4f9a-8f46-c7194b0dc0a5%22%7D; XSRF-TOKEN=eyJpdiI6ImdJYzV2R2xjWHhOSTFKZTFsOFhRcXc9PSIsInZhbHVlIjoiZHhyajVkTTMrQUNXajducW5NeTk2b2JDVHlkVGhYcU9xdkFmU2pEMlBGQ0RIY1NrWlBQaFc2Y2R5MmZsRFFoUE1KS25KcGZjWDJscmRhV2ZrckNJa3c9PSIsIm1hYyI6IjQzODMyMDU5OTI4YzIwOWFkZDA5ODY2YTA1M2QyNjY1MGM5YWVjYzk0NGQ5MmE4MDY3NDE4M2M1ODAyMGZlZTgifQ%3D%3D; aid=eyJpdiI6IndQU3hKYmtDTHdcL1ZHczZtajc4K2JnPT0iLCJ2YWx1ZSI6ImlJQ1ZcL3NHQjE3emg5cDZKdzRJeUllTXBDNmRPcm9aM1JiWmx2OStGK0J5TnJEWWdxZ1FsbDFCUE5FMnlucEk2RFJNN015R0MrWXFNNUhNaXAxeitBQT09IiwibWFjIjoiZDkxYThiOGI0ZjRmNDYyYzU5M2UwYWVlMjJiNjRjYTcwNDFlZDg0ZDg2YTRjOGY0ODkzMWRmNDc5MTM1MmY3YiJ9; appservername=app1; region=1'

        headers = {
            'Accept': r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': r'gzip, deflate, br',
            'Accept-Language': r'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': r'max-age=0',
            'Connection': r'keep-alive',
            'Cookie': cookie,
            'Host': r'www.perekrestok.ru',
            'Referer': r'https://www.perekrestok.ru/',
            'Sec-Fetch-Mode': r'navigate',
            'Sec-Fetch-Site': r'same-origin',
            'Sec-Fetch-User': r'?1',
            'Upgrade-Insecure-Requests': r'1',
            'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            }

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
                price_dict = dict()

                try:
                    price_dict['site_title'] = wspex_space(
                        soup.find('h1', {'class': re.compile('js-product__title\s+xf-product-card__title')}).text)
                except:
                    print(soup)

                print('site_title:', price_dict['site_title'])
                products_div = soup.find('div', {'class': 'xf-product__cost xf-product-cost'})
                if not products_div:
                    print('no products_div!')
                    # print(soup)
                    continue


                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title
                div_sale = products_div.find('div', {'class': 'xf-price xf-product-cost__prev js-product__old-cost'})
                if div_sale is not None:
                    # print('div-sale:', div_sale)
                    price_dict['price_old'] = float(div_sale.get('data-cost'))
                else:
                    price_dict['price_old'] = ''


                div_new = products_div.find('div',
                                            {'class': 'xf-price xf-product-cost__current js-product__cost _highlight'})
                if div_new is None:
                    div_new = products_div.find('div', {
                        'class': re.compile('xf-price\s+xf-product-cost__current\s+js-product__cost\s*')})

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