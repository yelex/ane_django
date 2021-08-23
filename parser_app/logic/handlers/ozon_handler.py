from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from tqdm import tqdm
import random
import os
from parser_app.logic.handlers.tools import wspex, wspex_space, get_proxy, get_my_ip
from parser_app.logic.global_status import Global
from fake_useragent import UserAgent
import requests
import ssl
import brotli # for decompress ozon response

ssl._create_default_https_context = ssl._create_unverified_context

class OzonHandler():
    # def option_chrome(self, proxy):
        # chromeOptions = webdriver.ChromeOptions()
        # chromeOptions.add_argument('--proxy-server=%s' % proxy)
        # return chromeOptions

    def get_proxy(self):  # опционально, если понадобится прокси
        success = False
        while True:
            driver = webdriver.Chrome(executable_path=Global().path_chromedriver)
            driver.get("https://hidemyna.me/ru/proxy-list/?maxtime=300&ports=3128..")
            while True:
                # time.sleep(1)
                if "maxtime" in driver.page_source:
                    ip_list = re.findall(r'\d{2,3}[.]\d{2,3}[.]\d{2,3}[.]\d{2,3}', driver.page_source)
                    break
            driver.quit()

            for it in range(5):
                print('it =', it)
                proxy = random.choice(ip_list[1:]) + ":3128"
                success = False

                driver = webdriver.Chrome(executable_path=Global().path_chromedriver,
                                          chrome_options=Global().chrome_options)
                driver.get("https://ozon.ru")
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "__nuxt"))
                    )
                    success = True
                    break
                finally:
                    driver.quit()
                if success == True:
                    break

            if success == True:
                break
            else:
                continue
        print('good proxy: {}'.format(proxy))
        driver.quit()
        return (proxy)

    def tnout(self, s):  # убрать \n и \t
        a = re.sub('\n', '', ' '.join(s.split()))
        a = re.sub('\t', '', ' '.join(a.split()))
        return a

    def extract_products(self, max_prod=200):
        path_sfb = os.path.join(Global().base_dir, r'description/urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')

        list_urls = sfb_df.fillna('')[sfb_df.fillna('')['URL'].str.contains('ozon')]['URL'].values

        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        # proxy = self.get_proxy()
        # options = webdriver.ChromeOptions()
        # proxy = get_proxy('http://ozon.ru') # если понадобится прокси
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
        # options.add_argument('--proxy-server=%s' % proxy)

        driver = webdriver.Chrome(executable_path=Global().path_chromedriver,
                                  chrome_options=Global().chrome_options)  # , chrome_options=self.option_chrome(proxy))
        headers = {'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Connection': 'keep-alive',
                    'Content-Length': '0',
                    'Content-Type': 'text/plain;charset=UTF-8',
                    'Cookie': 'VID=2sh8IT0p8Onz00000R0sD4Hz:::0-0-0-488ab53:CAASEHvKorqttCaEwEL2wJ6qbw4aYEYiFwEtz7TKHBhnYwAYnAgVVEuKyZrBcONGWUUBX029Gk4KsHhjdQh_fW9RjIhUo6VvoSrdaUUUUYqcsG2cXHtv8Ia63PlNuSqMs1NxSJhNdmF8Du_UA4pAGm9zRdfhzw',
                    'Host': 'top-fwz1.mail.ru',
                    'Origin': 'https://www.ozon.ru',
                    'Referer': 'https://www.ozon.ru/category/chulki-i-kolgotki-7539/?text=%D0%9A%D0%BE%D0%BB%D0%B3%D0%BE%D1%82%D0%BA%D0%B8+Le+Cabaret+%D1%87%D0%B5%D1%80%D0%BD%D1%8B%D0%B9%2C+20+den',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36}'}
        store = 'ozon'

        id_n = 0

        for url in tqdm(list_urls):

            id_n += 1

            driver.get(url)
            soup = BeautifulSoup(driver.page_source, 'lxml')

            category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('ozon')]['cat_title'].iloc[id_n-1]

            print('\n{} ...'.format(category_title))

            i = 0

            # print(url)
            n = int(re.search('\d+', re.search('\d+ товар[а-я]*', soup.text)[0])[0])
            num_pages = int(round(n/36, 0))
            if num_pages<n/36:
                num_pages+=1
                print('num_pages:', num_pages)
            print('amount of items: ', n)
            for num_page in range(num_pages):
                time.sleep(3)
                num_page += 1
                print(num_page)
                if num_page > 1:
                    if '?' in url:
                        url_page = url.split('?')[0] + f'?page={num_page}&' + url.split('?')[-1]
                    else:
                        url_page = url + f'?page={num_page}'
                    print('url_page:', url_page)
                    driver.get(url_page)

                # print(soup)
                max_tiles=0
                while True:
                    time.sleep(1)

                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    tiles_list = soup.findAll('div', {'class': 'a0s9'})
                    if num_page != num_pages:
                        print('1', len(tiles_list))
                        if len(tiles_list) == 36:
                            break
                    else:
                        print('2',len(tiles_list))
                        print('n-i=', n-i)
                        if len(tiles_list) == n-i:
                            break
                        if len(tiles_list) > n-i:
                            max_tiles = n-i
                            break
                    driver.get(url_page)
                    print('repeat url:', url_page)
                #     tiles_list = soup.findAll('div', {'class': 'a0s9'})
                    # контейнер для одного продукта
                print('len(tiles_list)', len(tiles_list))
                if max_tiles>0:
                    tiles_list = tiles_list[:max_tiles]
                for tile in tiles_list:
                    i += 1
                    price_dict = dict()
                    # print(tile)

                    try:
                        price_dict['price_old'] = tile.find('div', {'class': 'a0y7'}).text
                        # print('price old:', price_dict['price_old'])
                        price_dict['price_old'] = int(re.search('\d+', wspex(price_dict['price_old']))[0])
                    except:
                        price_dict['price_old'] = ''

                    price_dict['site_unit'] = 'шт.'
                    price_dict['site_code'] = store
                    price_dict['category_id'] = int(
                        sfb_df.fillna('')[sfb_df.fillna('')['URL'].str.contains('ozon')].index[id_n])
                    # print('category_id: ',price_dict['category_id'])
                    price_dict['date'] = Global().date
                    price_dict['type'] = 'non-food'


                    price_dict['site_title'] = self.tnout(tile.find('a', {'class': "a2g0 tile-hover-target"}).text)

                    price_dict['category_title'] = category_title
                    try:
                        price_dict['price_new'] = tile.find('span', {'class': 'a0y4 a0y5'}).text
                        price_dict['price_new'] = int(re.match('\d+', self.tnout(wspex(price_dict['price_new'])))[0])
                    except:

                        price_dict['price_new'] = tile.find('span', {'class': 'a0y4'}).text
                        price_dict['price_new'] = int(re.match('\d+', self.tnout(wspex(price_dict['price_new'])))[0])

                    try:
                        price_dict['site_link'] = 'https://www.ozon.ru' + tile.find('a',
                                                                                    {'class': 'a2g0 tile-hover-target'}).get(
                            'href')
                    except:
                        print(price_dict['site_title'] + ' Has not site_link!!!')
                        # print(soup)
                        price_dict['site_link'] = price_dict['site_title']
                    print('site_title[{}]: {}\ncategory_title: {}\nprice_new: {}'
                          '\nprice_old: {}\nsite_link: {}\n\n'.format(i,
                                                                    price_dict['site_title'],
                                                                    price_dict['category_title'],
                                                                    price_dict['price_new'],
                                                                    price_dict['price_old'],
                                                                    price_dict['site_link']))
                    res = res.append(price_dict, ignore_index=True)

        return res

    def extract_product_page(self):
        site_code = 'ozon'
        desc_df = Global().desc_df
        links_df = Global().links
        links_df = links_df[links_df['site_link'].str.contains(site_code)]

        if Global().max_links != None:
            links_df = links_df.iloc[:Global().max_links]
        category_ids = links_df.category_id.unique()
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                                    'site_title', 'price_new', 'price_old', 'site_unit',
                                    'site_link', 'site_code'])

        if Global().is_selenium_ozon is True:
            driver = webdriver.Chrome(executable_path=Global().path_chromedriver,
                                      chrome_options=Global().chrome_options)

        #, chrome_options=self.option_chrome(proxy))

        # ua = UserAgent(verify_ssl=False)
        # header = {
        #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        #     'accept-encoding': 'gzip, deflate, br',
        #     'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        #     'cache-control': 'max-age=0',
        #     'cookie': 'nlbi_1101384=nMCUfawHylboXscAyZtWRQAAAADULGu6hNydKBIS55YeLZJg; visid_incap_1101384=W5yRhcwfRrKKb0DX8Q3BnQBi52AAAAAAQUIPAAAAAAAbE1IuoFZ/7IrCe3zJwzBe; incap_ses_768_1101384=EDgCOxY1gUiOphuWS3yoCgBi52AAAAAAf44l/wKIx9AeZNfNLWgj9g==; __Secure-access-token=3.0.T-KiWYofRlKVSzlSNQdppw.28.l8cMBQAAAABg52ICGkZT0KN3ZWKgAICQoA..20210708223722.ObT4s6K91cYcpagT-iQ3CKBZ4MBIjR_L8NvxnHM2HGY; __Secure-refresh-token=3.0.T-KiWYofRlKVSzlSNQdppw.28.l8cMBQAAAABg52ICGkZT0KN3ZWKgAICQoA..20210708223722.30dS_d1zG6-y39NqVfU4xRZvbEcmn7rYzY4hyNJtiwk; __Secure-ab-group=28; __Secure-user-id=0; xcid=b1330628b1a2692f6557f8169e96bde9; __Secure-ext_xcid=b1330628b1a2692f6557f8169e96bde9; _gcl_au=1.1.779718125.1625776650; _ga=GA1.2.599202631.1625776650; _gid=GA1.2.137797260.1625776651; cnt_of_orders=0; isBuyer=0; tmr_lvid=837623c478bf17c1e0075b46d1b1cfdf; tmr_lvidTS=1625776656643; __exponea_etc__=05906026-cd7f-4c80-93d0-2586b22ad6d2; __exponea_time2__=1.0410804748535156; _fbp=fb.1.1625776660025.704811238; tmr_detect=0%7C1625776665697; _ga_JNVTMNXQ6F=GS1.1.1625776649.1.1.1625776699.0; RT="z=1&dm=ozon.ru&si=1aa9d7b4-2632-4a85-a92a-9aef525090c8&ss=kqvdfoda&sl=1&tt=6wq&bcn=%2F%2F6852bd13.akstat.io%2F&ld=72s&nu=6i3y0u4s&cl=17xw&ul=5rzn"; tmr_reqNum=5',
        #     'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        #     'sec-ch-ua-mobile': '?0',
        #     'sec-fetch-dest': 'document',
        #     'sec-fetch-mode': 'navigate',
        #     'sec-fetch-site': 'none',
        #     'sec-fetch-user': '?1',
        #     'upgrade-insecure-requests': '1',
        #     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        # } # true

        header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        }
        proxies = None # get_proxy(links_df[links_df.category_id == category_ids[0]].site_link.values[0]) # None #

        h1_class = 'e8i9'
        price_new_class_sale = 'c2h5 c2h6'
        price_new_class = price_new_class_sale.split(' ')[0]
        price_old_class = 'c2h8'
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values
            category_title = desc_df.loc[cat_id, 'cat_title']
            print("{}... ".format(category_title))

            i = 0

            while i + 1 <= len(url_list):
                # get_my_ip()
                time.sleep(1 + 2 * np.random.rand(1)[0])
                href_i = url_list[i]
                print(href_i)
                if Global().is_selenium_ozon is True:
                    driver.get(href_i)
                    soup = BeautifulSoup(driver.page_source, 'lxml')

                else:
                    try:

                        if proxies is not None:
                            get_my_ip()
                            r = requests.get(href_i, proxies=proxies, headers=header)  # CRITICAL
                        else:
                            r = requests.get(href_i, headers=header)
                    except:
                        while 'Incapsula' in r.content:
                            print('Damn, Incapsula!')
                            try:
                                proxies = get_proxy(href_i)
                                # time.sleep(10)
                                r = requests.get(href_i, proxies=proxies, headers=header)
                                if r.status_code == 200:
                                    break
                                else:
                                    print('r.status_code:', r.status_code)
                            except:
                                continue
                    try:
                        soup = BeautifulSoup(brotli.decompress(r.content), 'lxml')
                    except Exception as e:
                        print('Exception:', e)
                        print(r.content)
                        raise ImportError

                # print(soup)
                price_dict = dict()
                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title

                i += 1
                try:
                    if soup.find('h1', {'class': h1_class}) is not None:
                        price_dict['site_title'] = wspex_space(soup.find('h1', {'class': h1_class}).text)

                    print('site_title:', price_dict['site_title'])
                except:
                    # print(soup)
                    print('except sitetitle not found')
                    if 'Такой страницы не существует' in soup.text:
                        print('Такой страницы не существует!')

                    if 'Incapsula' in soup.text:
                        print('Incapsula detected!')
                        time.sleep(3 + np.random.rand(1)[0])
                        proxies = get_proxy(href_i)

                        i -= 1
                    if soup.find('li', {'class': 'links-item'}) is None:
                        print('links-item place')

                    continue

                div_new = soup.find('span', {'class': price_new_class_sale})

                if div_new is None:
                    div_new = soup.find('span', {'class': price_new_class})

                if div_new is None:
                    print('Товар исчез!\n')
                    continue

                if re.search('\d+', wspex(div_new.text)) is None:
                    print('Нет цифр в цене!\n')
                    continue

                if 'Этот товар закончился' in soup.text:
                    print('Этот товар закончился\n')
                    continue

                if 'Товар не доставляется в Ваш город' in soup.text:
                    print('Товар не доставляется в Ваш город\n')
                    continue

                if soup.find('div', {'class': 'c2e2'}):
                    print('Товар тупо закончился\n')
                    continue

                # if 'Товар закончился' in soup.text:
                #     print('except4')
                #     print('Товар закончился!\n')
                #     continue
                # print('din_new:\n', div_new)
                '''
                soup.find('span', {
                'class': 'price-number'})
                '''

                div_old = soup.find('span', {'class': price_old_class})

                if div_old is not None:
                    price_dict['price_old'] = int(re.search('\d+', wspex(div_old.text))[0])
                else:
                    price_dict['price_old'] = ''

                price_dict['price_new'] = int(re.search('\d+', wspex(div_new.text))[0])

                price_dict['site_unit'] = 'шт.'
                price_dict['site_link'] = href_i  # показывает название товара и ссылку на него
                price_dict['type'] = 'non-food'
                print('price_new: {}\nprice_old: {}\nunit: {}\n'.format(
                    price_dict['price_new'],
                    price_dict['price_old'],
                    price_dict['site_unit']))
                res = res.append(price_dict, ignore_index=True)

        print('OZON has successfully parsed')
        return res