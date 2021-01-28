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
import os
from parser_app.logic.handlers.tools import wspex, wspex_space, get_proxy, get_my_ip
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
        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
        proxies = None # get_proxy(links_df[links_df.category_id == category_ids[0]].site_link.values[0])

        h1_class = 'b3a8'
        price_new_class_sale = 'b3d b3n5'
        price_new_class = price_new_class_sale.split(' ')[0]
        price_old_class = 'b3d5'
        for cat_id in tqdm(category_ids):  # испр
            url_list = links_df[links_df.category_id == cat_id].site_link.values
            category_title = desc_df.loc[cat_id, 'cat_title']
            print("{}... ".format(category_title))

            i = 0

            while i + 1 <= len(url_list):
                # get_my_ip()
                href_i = url_list[i]
                print(href_i)
                if Global().is_selenium_ozon is True:
                    driver.get(href_i)
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                else:
                    try:
                        time.sleep(3)
                        if proxies is not None:
                            print(proxies)
                            r = requests.get(href_i, proxies=proxies, headers=header)  # CRITICAL
                        else:
                            r = requests.get(href_i, headers=header)
                    except:
                        for i in range(2):
                            print('im here!')
                            try:
                                proxies = get_proxy(href_i)
                                # time.sleep(10)
                                r = requests.get(href_i, proxies=proxies, headers=header)
                                if r.status_code == 200:
                                    break
                                else:
                                    print('r.status_code:', r.status_code)
                                    html = r.content
                                    soup = BeautifulSoup(html, 'lxml')
                                    print('soup:\n', soup)
                            except:
                                continue
                    html = r.content
                    soup = BeautifulSoup(html, 'lxml')



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
                    print('except sitetitle not found')
                    if 'Такой страницы не существует' in soup.text:
                        print('Такой страницы не существует!')

                    if 'Incapsula' in soup.text:
                        print('Incapsula detected!')
                        time.sleep(10)
                        proxies = get_proxy(href_i)

                        i -= 1
                    if soup.find('li', {'class': 'links-item'}) is None:
                        print('links-item place')

                        # while True:
                        # for iterr in range(2):
                        #     proxies = get_proxy(href_i)
                        #     time.sleep(3)
                        #     r = requests.get(href_i, proxies=proxies, headers=header)
                        #     if r.status_code == 200:
                        #         break
                        #     else:
                        #         print('r.status_code:', r.status_code)
                    continue

                # div_new = soup.find('span', {'data-test-id': 'saleblock-first-price'})
                # print('soup:\n', soup)
                # if 'Товар закончился' in soup.text:
                #     print('Товар точно закончился!')
                #     continue

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