import pandas as pd
from datetime import datetime, timedelta
import os


class Global:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.links = pd.read_csv(os.path.join(self.base_dir, 'final_links.csv'), sep=';')
        self.path_desc = os.path.join(self.base_dir, r'description\categories.csv')
        self.desc_df = pd.read_csv(self.path_desc, sep=';', index_col='id')
        self.date = datetime.now().date()-timedelta(days=0)
        self.max_links = 1
        self.is_selenium = False
        self.path_chromedriver = 'C:\\Users\\evsee\\Downloads\\chromedriver.exe'


