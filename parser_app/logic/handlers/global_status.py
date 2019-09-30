import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone

import os


class Global:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.links = pd.read_csv(os.path.join(self.base_dir, r'description\final_links.csv'), sep=';', index_col=0)
        self.path_desc = os.path.join(self.base_dir, r'description\categories.csv')
        self.desc_df = pd.read_csv(self.path_desc, sep=';', index_col='id')
        self.date = timezone.now().date() # -timedelta(days=0)
        self.max_links = 2
        self.is_selenium_okey = False
        self.is_selenium_utkonos = True
        self.path_chromedriver = 'C:\\Users\\evsee\\Downloads\\chromedriver.exe'


