from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from parser_app.logic.global_status import Global
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

class PiluliHandler():

    def extract_products(self):

        path = Global().path_chromedriver  # здесь вставить путь к chomedriver

        path_sfb = os.path.join(Global().base_dir, r'description/urls.csv')
        sfb_df = pd.read_csv(path_sfb, sep=';', index_col='id')

        #keywords = df_desc.loc[['7', '18', '21']]['Ключевы слова, которые должны присутствовать'].values
        urls = sfb_df.fillna('')[sfb_df['URL'].fillna('').str.contains('piluli')]['URL'].values
        ids = sfb_df.fillna('')[sfb_df['URL'].fillna('').str.contains('piluli')].index.astype(int)

        category_titles = sfb_df.fillna('')[sfb_df['URL'].fillna('').str.contains('piluli')]['cat_title'].values

        # запуск парсинга
        res = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

        # options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        #options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(executable_path=path, chrome_options=Global().chrome_options)

        for index, link in enumerate(urls):
            price_dict = dict()
            print(link)
            driver.get(link)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            price_dict['category_id'] = ids[index]
            price_dict['date'] = Global().date
            price_dict['site_code'] = 'piluli'
            price_dict['site_unit'] = 'шт.'
            price_dict['type'] = 'non-food'
            price_dict['category_title'] = category_titles[index]
            price_dict['site_link'] = link
            price_dict['site_title'] = soup.find('h1', {'id': 'offer-title'}).text
            price_dict['price_new'] = int(soup.find('span', {'id': 'products_price'}).text)
            price_dict['price_old'] = int(soup.find('span', {'class': 'old-price'}).text) if soup.find('span', {'class': 'old-price'}).text != '\n' else ''

            res = res.append(price_dict, ignore_index=True)

        driver.quit()

        return res