from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime, timedelta
from parser_app.logic.handlers.tools import filter_flag, get_proxy, tofloat, wspex_space
from parser_app.logic.global_status import Global
from tqdm import tqdm
import re


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
        path_sfb = os.path.join(Global.base_dir, r'description\urls.csv')
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
        site_code = 'perekrestok'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]
        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        proxies = get_proxy('https://www.perekrestok.ru/')
        # proxies = None
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values
            # url_list = ['https://www.okeydostavka.ru/webapp/wcs/stores/servlet/ProductDisplay?urlRequestType=Base&catalogId=12051&categoryId=84082&productId=44245&errorViewName=ProductDisplayErrorView&urlLangId=-20&langId=-20&top_category=65054&parent_category_rn=65054&storeId=10151']

            category_title = desc_df.loc[cat_id, 'cat_title']

            print("{}... ".format(category_title))

            # print(' id_n =', id_n)
            i = 0

            while i + 1 <= len(url_list):

                href_i = url_list[i]
                print('site_link: ', href_i)
                i += 1

                try:
                    if proxies!=None:
                        r = requests.get(href_i, proxies=proxies)  # CRITICAL
                    else:
                        r = requests.get(href_i)
                except:
                    proxies = get_proxy('https://www.perekrestok.ru/')
                    r = requests.get(href_i, proxies=proxies)
                html = r.content

                soup = BeautifulSoup(html, 'lxml')

                products_div = soup.find('div', {'class': 'xf-product-main js-product__zoom-container'})
                if not products_div:
                    print('no products_div!')
                    break

                price_dict = dict()
                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title
                div_sale = products_div.find('div', {'class': 'xf-price xf-product-cost__prev'})
                if div_sale is not None:
                    # print('div-sale: ',div_sale)
                    price_dict['price_old'] = float(div_sale.get('data-cost'))
                else:
                    price_dict['price_old'] = ''

                price_dict['site_title'] = wspex_space(
                    products_div.find('h1', {'class': 'js-product__title xf-product-card__title'}).text)
                div_new = products_div.find('div',
                                            {'class': 'xf-price xf-product-cost__current js-product__cost _highlight'})
                if div_new is None:
                    div_new = products_div.find('div', {
                        'class': re.compile('xf-price\s+xf-product-cost__current\s+js-product__cost\s*')})
                if div_new is None:
                    continue
                price_dict['price_new'] = float(div_new.get('data-cost'))
                price_dict['site_unit'] = wspex_space(div_new.get('data-type'))
                price_dict['site_link'] = href_i  # показывает название товара и ссылку на него
                price_dict['type'] = 'food'
                print('site_title: {}\nprice_new: {}\nprice_old: {}\nunit: {}\n'.format(price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old'],
                                                                                        price_dict['site_unit']))
                res = res.append(price_dict, ignore_index=True)

        print('PEREKRESTOK has successfully parsed')
        return res