from bs4 import BeautifulSoup
import pandas as pd
import requests
import os
from .global_status import Global
import re
from datetime import datetime
from fake_useragent import UserAgent


class Services():
    def __init__(self):
        self.path_sfb = os.path.join(Global().base_dir, r'description\urls.csv')

    def wspex(self,x):
        """
        White SPace EXclude
        :param x: string
        :return: string x without any whitespaces
        """
        return re.sub(u'\u200a', '', ''.join(x.split()))

    def wspex_space(self,x):
        return re.sub(u'\u200a', '', ' '.join(str(x).split()))

    def get_df(self):

        sfb_df = pd.read_csv(self.path_sfb, sep=';', index_col='id')
        serv_df = sfb_df[sfb_df['type'] == 'services']

        list_url = serv_df['URL'].values
        final_df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                           'site_title', 'price_new', 'price_old', 'site_unit',
                           'site_link', 'site_code'])

        #mgts
        n=0
        url=list_url[n]
        html=requests.get(url, headers={'User-Agent': UserAgent().chrome}).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        price_list=soup.findAll('div',{'class':'slider_slide'})#0 заменить
        for price_elem in price_list:
            if price_elem.findAll('div',{'class':'texts'})[0].text=='Безлимитный':
                price_dict=dict()
                price_dict['date']=Global().date
                price_dict['site_code']='services'
                id_n=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
                price_dict['category_id'] = id_n
                price_dict['category_title'] = serv_df['cat_title'].loc[price_dict['category_id']]
                price_dict['type'] = 'services'
                price_dict['site_title']=price_elem.findAll('div',{'class':'texts'})[0].text
                price_dict['price_new']=int(price_elem.findAll('div',{'class':'slider_price_val'})[0].text)
                price_dict['price_old'] = ''
                price_dict['site_unit']=price_elem.findAll('div',{'class':'slider_price_rub1'})[0].text+'/'+price_elem.findAll('div',{'class':'slider_price_rub2'})[0].text
                price_dict['site_link']=url
                final_df=final_df.append(price_dict,ignore_index=True)
                break

        #Помывка в бане в общем отделении, билет	http://legkiipar.ru/menraz.html
        try:
            n=1
            url=list_url[n]
            html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
            soup=BeautifulSoup(html, 'lxml')#Будние дни с 08:00 до 22:00
            pattern=re.compile(r'Будние дни')
            price_dict=dict()
            price_dict['date']=Global().date
            price_dict['site_code']='services'
            price_dict['type'] = 'services'
            price_dict['site_title']=soup(text=pattern)[0]
            price_1=soup.findAll('span',{'class':'стиль6'})
            price_dict['price_new'] = re.findall('\d+',price_1[1].text)[0]
            price_dict['price_old'] = ''
            price_dict['site_unit']=re.findall('\d+ часа',price_1[4].text[:-1])[0]
            price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
            price_dict['category_title'] = serv_df['cat_title'].loc[price_dict['category_id']].values[0]
            price_dict['site_link']=url
            final_df=final_df.append(price_dict,ignore_index=True)
        except:
            print('DAMN! {} can not be parsed'.format(url))

        #Помывка в бане в общем отделении, билет	http://banya-lefortovo.ru/price.html
        n=2
        price_dict=dict()
        price_dict['date']=Global().date
        price_dict['site_code']='services'
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        pattern=re.compile(r'Русская общая баня')
        price_dict['site_title']=soup(text=pattern)[0]
        price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
        price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
        price_dict['type'] = 'services'
        price_dict['price_new']=int(re.findall('\d+',re.findall('\d+ рублей',soup(text=pattern)[0])[0])[0])
        price_dict['price_old']=''
        price_dict['site_unit']=re.findall('\d+ часа',soup(text=pattern)[0])[0]
        price_dict['site_link']=url
        final_df=final_df.append(price_dict,ignore_index=True)

        #Помывка в бане в общем отделении, билет	https://rzhevskie-bani.ru/rb/bani.html
        n=3
        price_dict=dict()
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        price_dict['price_new']=int(re.findall('\d+',soup.findAll('td',{'class':'price'})[0].text)[0])
        pattern=re.compile(r'Стоимость')
        soup.findAll('td')
        price_dict['date']=Global().date
        price_dict['site_code']='services'
        price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
        price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
        price_dict['site_title']=soup(text=pattern)[0]
        price_dict['type'] = 'services'
        price_dict['site_unit']=re.findall('(\d+.*\d часа)',soup(text=pattern)[0][-9:])[0]
        price_dict['site_link']=url
        final_df=final_df.append(price_dict,ignore_index=True)

        #Помывка в бане в общем отделении, билет	http://vorontsovskie-bani.ru/obshchestvennye-bani/muzhskoj-zal-pervyj-razryad
        n=4
        price_dict=dict()
        price_dict['date']=Global().date
        price_dict['site_code']='services'
        url=list_url[n]
        price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
        html=requests.get(url, headers={'User-Agent': UserAgent().chrome}).content
        soup=BeautifulSoup(html, 'lxml')
        price_div=soup.findAll('div',{'class':'price-head'})[0]
        price_dict['price_new']=int(re.findall('\d+',price_div.findAll('span',{'class':'price'})[0].text)[0])
        price_dict['price_old']=''
        price_dict['site_title']=price_div.find('p').text.replace('\xa0',' ')
        price_dict['site_unit']=re.findall('\d+ часа',price_dict['site_title'])[0]
        price_dict['type'] = 'services'
        price_dict['site_link']=url
        price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
        final_df=final_df.append(price_dict,ignore_index=True)

        #Постановка набоек, пара	https://masterskaya-obuvi.ru/tseny
        n=5
        price_dict=dict()
        price_dict['date']=Global().date
        price_dict['site_code']='services'
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
        price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
        for elem in soup.findAll('tr'):
            if re.findall('износоустойчивой резины',elem.text)!=[]:
                price_div=elem
                price_dict['site_title']=re.findall('[А-Яа-яёз(). ]+',elem.text)[0]
                price_dict['site_unit']=re.findall('[А-Яа-яёз(). ]+',elem.text)[1]
                price_dict['price_new']=int(price_div.findAll('td',{'width':"356"})[0].text)
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_link']=url
                break

        final_df=final_df.append(price_dict,ignore_index=True)

        #Постановка набоек, пара	https://masterskaya-obuvi.ru/tseny
        '''
        n=6
        price_dict=dict()
        price_dict['date']=Global().date
        price_dict['site_code']='services'
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
        price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
        for elem in soup.findAll('tr'):
            if re.findall('эконом',elem.text)!=[]:
                price_div=elem
                price_dict['site_title']=self.wspex_space(re.findall('[А-Яа-яёз(). ]+',price_div.findAll('td',{'align':'left'})[0].text)[0])
                price_text=price_div.findAll('strong')[0].text
                price_dict['price_new']=int(re.findall('\d+',price_text)[0])
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_unit']=re.findall('\([А-Яа-я]*\)',price_dict['site_title'])[0][1:-1]
                price_dict['site_link']=url
                break
        final_df=final_df.append(price_dict,ignore_index=True)
        '''

        #Билет на 1 поездку - мосгортранс
        n=7
        price_dict=dict()
        price_dict['site_code']='services'
        price_dict['date']=Global().date
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        #soup.findAll('td')#,{'class':'text-center'})[0]
        price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
        price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title']
        for elem in soup.findAll('td'):
            if re.findall('не более',elem.text)!=[]:
                price_div=elem
                site_title=price_div.text
                break

        for elem in soup.findAll('tr'):
            if re.findall('не более',elem.text)!=[]:
                price_div=elem
                price_dict['site_title']=price_div.find('td').text
                price_dict['price_new']=int(re.findall('\d{2,3}',price_div.text)[0])
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_unit']='поездка'
                price_dict['site_link']=url
                break
        final_df=final_df.append(price_dict,ignore_index=True)

        #стрижка
        n=8
        price_dict=dict()
        price_dict['site_code']='services'
        price_dict['date']=Global().date
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')

        #soup.findAll('td')#,{'class':'text-center'})[0]
        for elem in soup.findAll('tr'):
            if re.findall('(любой длины)',elem.text)!=[]:
                price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[-1])
                price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
                price_text=elem.text
                price_dict['site_title']=re.findall('[А-Яа-я ()]+',price_text)[0]
                price_dict['price_new']=re.findall('\d+',price_text)[0]
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_unit']='стрижка'
                price_dict['site_link']=url
                break
        final_df=final_df.append(price_dict,ignore_index=True)

        #стрижка
        n=9
        price_dict=dict()
        price_dict['site_code']='services'
        price_dict['date']=Global().date
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')

        for elem in soup.findAll('tr'):
            if re.findall('Женская',elem.text)!=[]:
                price_div=elem
                price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[0])
                price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
                price_dict['site_title']=price_div.find('td',{'class':'services-table__name'}).text
                price_dict['price_new']=int(self.wspex(price_div.find('td',{'class':'services-table__price services-table__price-small'}).text))
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_unit']='стрижка'
                price_dict['site_link']=url
                break
        final_df=final_df.append(price_dict,ignore_index=True)

        '''
        #стрижка
        n=10
        price_dict=dict()
        price_dict['site_code']='services'
        price_dict['date']=Global().date
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')
        for elem in soup.findAll('tr'):
            if re.findall('лопаток',elem.text)!=[]:
                price_div=elem
                price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(list_url[n-1])].index[0])
                price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title'].values[0]
                price_dict['site_title']=price_div.find('td',{'height':'17'}).text
                price_dict['price_new']=int(self.wspex(price_div.find('td',{'width':'157'}).text))
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_unit']='стрижка'
                price_dict['site_link']=url
                break
        final_df=final_df.append(price_dict,ignore_index=True)
        '''

        #Билет на 1 поездку - мосгортранс
        n=10
        price_dict=dict()
        price_dict['site_code']='services'
        price_dict['date']=Global().date
        url=list_url[n]
        html=requests.get(url).content#, headers={'User-Agent': UserAgent().chrome}
        soup=BeautifulSoup(html, 'lxml')

        for elem in soup.findAll('tr'):
            if re.findall('не более',elem.text)!=[]:
                price_div=elem
                price_dict['category_id']=int(serv_df[serv_df['URL'].str.contains(url)].index[-1])
                price_dict['category_title'] = serv_df.loc[price_dict['category_id']]['cat_title']
                price_dict['site_title']=price_div.find('td').text
                price_dict['price_new']=int(re.findall('\d{2,3}',price_div.text)[0])
                price_dict['price_old'] = ''
                price_dict['type'] = 'services'
                price_dict['site_unit']='поездка'
                price_dict['site_link']=url
                break
        final_df = final_df.append(price_dict,ignore_index=True)

        return final_df