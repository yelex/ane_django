import os

from bs4 import BeautifulSoup
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from tqdm import tqdm
import random
from parser_app.logic.handlers.tools import wspex, wspex_space, get_proxy
from parser_app.logic.global_status import Global
from fake_useragent import UserAgent
import requests
import ssl

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

        path_sfb = os.path.join(Global().base_dir, 'description', 'urls.csv')
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

        store = 'ozon'
        driver.implicitly_wait(30)

        id_n = -1

        for url in tqdm(list_urls[id_n + 1:]):
            flag = 0

            id_n += 1

            driver.get(url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.01);")

            category_title = sfb_df[sfb_df.fillna('')['URL'].str.contains('ozon')]['cat_title'].iloc[id_n]
            print('\n{} ...'.format(category_title))
            offset = 0

            soup = BeautifulSoup(driver.page_source, 'lxml')
            problem_array = []

            i = 0

            page_n = 0
            # print(url)

            while True:

                tiles_list = soup.findAll('div', {'class': 'tile'})[offset:]  # контейнер для одного продукта
                try:
                    n = int(re.search('\d+', re.search('\d+ товар[а-я]*', soup.text)[0])[0])
                except:
                    try:
                        n = int(re.search('\d+', soup.find('div', {'class': 'search-title'}).text)[0])
                    except:
                        print("ACHTUNG! category {} has not been parsed".format(category_title))
                        continue
                # print('amount of items: ', n)

                for tile in tiles_list:
                    i += 1
                    price_dict = dict()
                    # print(tile)

                    try:
                        price_dict['price_old'] = tile.find('div', {'data-test-id': 'tile-discount'}).text
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

                    try:
                        price_dict['site_title'] = self.tnout(tile.find('a', {'data-test-id': "tile-name"}).text)
                    except:
                        problem_array.append(url)
                        print('OOPS! url {} has not parsed site title'.format(url))
                        break
                    price_dict['category_title'] = category_title
                    price_dict['price_new'] = tile.find('span', {'class': 'total-price'}).text
                    price_dict['price_new'] = int(re.match('\d+', self.tnout(wspex(price_dict['price_new'])))[0])
                    if tile.find('a', {'class': 'full-cover-link'}) == None:
                        price_dict['site_link'] = ''
                        print("ACHTUNG! link has not parsed for site_title: {}".format(price_dict['site_title']))
                    else:
                        price_dict['site_link'] = 'https://www.ozon.ru' + tile.find('a',
                                                                                    {'class': 'full-cover-link'}).get(
                            'href')
                    '''print('site_title[{}]: {}\nprice_new: {}\nprice_old: {}\n\n'.format(i,price_dict['site_title'],
                                                                                        price_dict['price_new'],
                                                                                        price_dict['price_old']))'''
                    res = res.append(price_dict, ignore_index=True)

                if i >= n or i >= max_prod or flag == 1:
                    print('   parsing has ended!')
                    break

                offset = offset + len(tiles_list)

                if offset % 280 == 0 and offset != 0:
                    page_n += 11
                    url = url + '&page={}'.format(str(page_n))
                    driver.get(url)
                    print('\n   loading url:{}'.format(url))
                    offset = 0
                    while True:
                        time.sleep(1)

                        soup = BeautifulSoup(driver.page_source, 'lxml')

                        if soup.findAll('div', {'class': 'tile'}) != []:
                            break
                else:

                    scheight = 0.9

                    while True:

                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*{});".format(scheight))

                        soup = BeautifulSoup(driver.page_source, 'lxml')

                        if soup.findAll('div', {'class': 'tile'})[offset:] != []:
                            print("  offset: {}".format(offset))
                            break
                        if scheight < 1:
                            scheight += 0.01
                        else:
                            print('WARNING! Scrolling has not been executed (we are here)')
                            flag = 1
                            break

                        print(scheight)
                        time.sleep(1)

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
        # options = webdriver.ChromeOptions()
        # proxies = get_proxy('https://www.ozon.ru/')
        # options.add_argument('--headless')
        # options.add_argument('--proxy-server=%s' % proxy)
        if Global().is_selenium_ozon is True:
            driver = webdriver.Chrome(executable_path=Global().path_chromedriver,
                                      chrome_options=Global().chrome_options)  #, chrome_options=self.option_chrome(proxy))
        ua = UserAgent()
        header = {'User-Agent': str(ua.chrome)}
        proxies = None

        h1_class = 'b4j'
        price_new_class_sale = 'b4u8 b4w0'
        price_new_class = 'b4u8'
        price_old_class = 'b4v2'
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values
            category_title = desc_df.loc[cat_id, 'cat_title']
            print("{}... ".format(category_title))

            i = 0

            while i + 1 <= len(url_list):

                href_i = url_list[i]
                print(href_i)
                if Global().is_selenium_ozon is True:
                    driver.get(href_i)
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                else:
                    try:
                        # time.sleep(3)
                        if proxies is not None:
                            r = requests.get(href_i, proxies=proxies, headers=header)  # CRITICAL
                        else:
                            r = requests.get(href_i, headers=header)
                    except:
                        while True:
                            print('im here!')
                            try:
                                proxies = get_proxy(href_i)
                                time.sleep(3)
                                r = requests.get(href_i, proxies=proxies, headers=header)
                                if r.status_code == 200:
                                    break
                            except:
                                continue
                    html = r.content
                    soup = BeautifulSoup(html, 'lxml')

                i += 1

                # print(soup)
                price_dict = dict()
                price_dict['date'] = Global().date
                price_dict['site_code'] = site_code
                price_dict['category_id'] = cat_id
                price_dict['category_title'] = category_title


                try:
                    if soup.find('h1', {'class': h1_class}) is not None:
                        price_dict['site_title'] = wspex_space(soup.find('h1', {'class': h1_class}).text)

                    print('site_title:', price_dict['site_title'])
                except:
                    print('except sitetitle not found')
                    if 'Такой страницы не существует' in soup.text:
                        print('Такой страницы не существует!')
                        continue
                    # i -= 1
                    if soup.find('li', {'class': 'links-item'}) is None:
                        while True:
                            proxies = get_proxy(href_i)
                            time.sleep(3)
                            r = requests.get(href_i, proxies=proxies, headers=header)
                            if r.status_code == 200:
                                break
                            else:
                                print('r.status_code:', r.status_code)
                    continue

                # div_new = soup.find('span', {'data-test-id': 'saleblock-first-price'})
                # print('soup:\n', soup)
                # if 'Товар закончился' in soup.text:
                # print('Товар закончился!')
                # continue

                div_new = soup.find('span', {'class': price_new_class_sale})

                if div_new is None:
                    div_new = soup.find('span', {'class': price_new_class})

                if div_new is None:
                    print('Товар закончился!\n')
                    continue

                if re.search('\d+', wspex(div_new.text)) is None:
                    print('Товар закончился!\n')
                    continue
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