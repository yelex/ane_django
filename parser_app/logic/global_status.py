import pandas as pd
from datetime import datetime, timedelta, date
import os


class Global:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.links = pd.read_csv(os.path.join(self.base_dir, r'description\final_links.csv'), sep=';', index_col=0)
        self.gks_links = os.path.join(self.base_dir, r'description\gks_weekly_links.csv')
        self.path_desc = os.path.join(self.base_dir, r'description\categories.csv')
        self.desc_df = pd.read_csv(self.path_desc, sep=';', index_col='id')
        self.date = date(month=11, day=13, year=2019)  # datetime.now().date()-timedelta(days=0)
        self.max_links = 2
        self.is_selenium_ozon = False
        self.is_selenium_okey = False
        self.is_selenium_utkonos = False
        self.is_shutdown = False
        self.path_chromedriver = 'C:\\Users\\evsee\\Downloads\\chromedriver.exe'





