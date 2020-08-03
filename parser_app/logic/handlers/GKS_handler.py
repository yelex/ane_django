import json
import os
import time
import shutil
from datetime import date as Date
import datetime
from typing import Union, Optional, List, Dict, Tuple
import pandas as pd
import numpy as np

from parser_app.logic.global_status import create_webdriver
from parser_app.logic.handlers.handler_tools import get_empty_handler_DF, _extract_units_from_string


class GKS_handler_interface:

    def __init__(self):
        self._local_store: pd.DataFrame = None
        self._units_table: Dict[str, Tuple[str, float]] = {}
        self._load_local_store()

    def _construct_url(self, start_date: Date, end_date: Optional[Date] = None) -> str:
        """
        Construct url for handle data from gks site.
        :param start_date: Date - datetime.datetime.date range start date
        :param end_date: Date - datetime.datetime.date range end date
        :return: string - url for handler
        """
        raise NotImplemented

    def get_site_link(self) -> str:
        """
        Link to store in pd.DataFrame.
        :return: string - link
        """
        return r"https://showdata.gks.ru"

    def get_handler_name(self) -> str:
        """
        Handler name
        :return: string - hnadler name
        """
        raise NotImplemented

    def transform_date_for_data(self, date: Date) -> Date:
        """
        Actually gks base have problem. The problem is in data updating.
        For example if you request weekly data in 3th day of week you wiil recive None.
            because week is not ended and data isn't computed yet (on gks site).
        So before requesting date this hadler will transform date.
        For example for weekly data, it will subtract 7days from current date,
            in order to have real data.
        :param date: date to transform
        :return: date for that we really will request data price
        """
        raise NotImplemented

    @staticmethod
    def _create_empty_df() -> pd.DataFrame:
        cat_with_kw = pd.read_csv(
            os.path.join('parser_app', 'logic', 'description', 'category_with_keywords.csv')
        )
        cat_titles = list(cat_with_kw['cat_title'])
        return pd.DataFrame(columns=['date_range_start', 'date_range_end', *cat_titles])

    def _get_path_to_local_store(self) -> str:
        """
        Retrurn string - path to local folder for this handler.
        :return: string - path
        """
        return os.path.join("parser_app", "logic", "gks_store", self.get_handler_name())

    def get_df(self) -> pd.DataFrame:
        """
        Return pd.DataFrame with prices for current date on all categories provided in `category_with_keywords.csv`
        :return: pd.DateFrame
        """
        self.update()
        df = get_empty_handler_DF()
        cat_with_kw = pd.read_csv(
            os.path.join('parser_app', 'logic', 'description', 'category_with_keywords.csv')
        )
        now_date = datetime.datetime.now().date()
        data_date = self.transform_date_for_data(now_date)
        for _, category_row in cat_with_kw.iterrows():
            units = self._units_table.get(category_row['cat_title'], ('шт', 1))

            new_price = self.get_cat_price_on_date(
                category_row['cat_title'],
                data_date,
            )
            old_price = self.get_cat_price_on_date(
                category_row['cat_title'],
                data_date - datetime.timedelta(days=7),
            )

            if new_price is None or old_price is None:
                continue

            df = df.append(
                ignore_index=True,
                other={
                    'date': now_date.strftime("%Y-%m-%d"),
                    'type': category_row['type'],
                    'category_id': int(category_row['id']),
                    'category_title': category_row['cat_title'],
                    'site_title': self.get_handler_name(),
                    'price_new': new_price,
                    'price_old': old_price,
                    'site_unit': f"{units[0]} {units[1]}",
                    'site_link': self.get_site_link(),
                    'site_code': self.get_handler_name(),
                    'miss': False,
                }
            )
        return df

    def get_last_updated_day(self) -> Date:
        assert self._local_store is not None
        if len(self._local_store) == 0:
            return datetime.datetime(year=1970, month=1, day=1).date()
        to_date = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date()
        return self._local_store['date_range_end'].apply(to_date).max()

    def update(self) -> None:
        assert self._local_store is not None
        now_date = datetime.datetime.now().date()
        transformed_now = self.transform_date_for_data(now_date)
        if transformed_now > self.get_last_updated_day():
            self._update_local_store(now_date - datetime.timedelta(days=50), transformed_now)

    @staticmethod
    def get_week_start(date: Date) -> Date:
        """
        Convert date to nearest in past Monday.
        """
        return date - datetime.timedelta(days=date.weekday())

    @staticmethod
    def _construct_filter_for_weekly_dates(start_date: Date, end_date: Optional[Date] = None) -> str:
        """
        Construct strange date format for gks site.
        Automatically convert start_date to nearest in past Monday.

        :param start_date: start of loaded range
        :param end_date: end of loaded range
        :return: string to insert into gks url request
        """
        if end_date is None:
            end_date = datetime.datetime.now().date()

        week_end = r"+00%3A00%3A00%7C-58"
        sep = "%2C"
        week_delta = datetime.timedelta(days=7)

        cur = GKS_handler_interface.get_week_start(start_date)
        ans = cur.strftime("%Y-%m-%d") + week_end
        while True:
            cur += week_delta
            if cur > end_date:
                break
            ans += sep

            ans += cur.strftime("%Y-%m-%d") + week_end
        return ans

    def _load_local_store(self) -> None:
        """
        Load pd.DataFrame with cached price and gks units from local files.
        If no local files presented, create empty objects.
        :return: None
        """
        if not os.path.exists(self._get_path_to_local_store()):
            os.makedirs(self._get_path_to_local_store())
            self._local_store = GKS_handler_interface._create_empty_df()
            self._units_table = dict()
            self._save_local_store()
            return

        if self._local_store is None:
            self._local_store = pd.read_csv(
                os.path.join(self._get_path_to_local_store(), f'{self.get_handler_name()}_price.csv'),
            )

        if self._units_table is None:
            self._units_table = json.load(
                open(os.path.join(self._get_path_to_local_store(), f'{self.get_handler_name()}_units.json'), 'r'),
            )

    def _save_local_store(self) -> None:
        """
        Save local (cached, in-RAM) objects to files in special folders.
        :return: None
        """

        if self._local_store is not None:
            self._local_store.to_csv(
                os.path.join(self._get_path_to_local_store(), f'{self.get_handler_name()}_price.csv'),
                index=False,
            )

        if self._units_table is not None:
            json.dump(
                self._units_table,
                open(os.path.join(self._get_path_to_local_store(), f'{self.get_handler_name()}_units.json'), 'w'),
            )

    def get_cat_price_on_date(self, category: str, date: Date) -> Union[None, float]:
        """
        Get price for category on provided date.
        :param category: string - category title
        :param date: Date - datatime.datetime.date - date on whitch you wand to load price
        :return: None if where no any price, or some erroe occure, else float - price
        """
        assert self._local_store is not None
        to_date = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date()
        try:
            self._local_store['date_range_start'] = self._local_store['date_range_start'].apply(to_date)
        except:
            pass
        try:
            self._local_store['date_range_end'] = self._local_store['date_range_end'].apply(to_date)
        except:
            pass

        week_row = self._local_store[np.logical_and(
            self._local_store['date_range_start'] <= date,
            date < self._local_store['date_range_end'],
        )]
        if week_row is None:
            # fixme log
            print(f'no such week in local store: date {date}')
            return None

        if category not in week_row.columns:
            # fixme log
            print(f'unknown category: {category}')
            return None

        try:
            value = week_row.iloc[0][category]
            if pd.isna(value):
                # fixme log
                print(f'This category is NaN: {category}')
                return None

            return float(value)
        except ValueError:
            return None

    def _update_local_store(self, start_date: Date, end_date: Date) -> None:
        """
        Load to local folder prices from gks site.
        :param start_date: date of range start
        :param end_date: end of date (is None, today is used)
        :return: None, just save all to local files
        """
        assert self._local_store is not None
        path_to_download_folder = os.path.join(
            os.path.abspath(os.curdir), 'parser_app', 'logic', 'gks_auto_download',
        )
        if os.path.exists(path_to_download_folder):
            shutil.rmtree(path_to_download_folder)
        os.makedirs(path_to_download_folder)

        driver = create_webdriver(download_path=path_to_download_folder)
        gks_url = self._construct_url(start_date, end_date)
        driver.get(gks_url)
        time.sleep(60)
        driver.find_element_by_class_name("fa-download").click()
        time.sleep(60)

        assert len(os.listdir(path_to_download_folder)) >= 1, \
            f"Problems with loading, no file in expected folder :\n{path_to_download_folder}\n***\n"

        # driver.quit()
        print(f'{self.get_handler_name()} -> exit driver, start to extract downloaded data')

        path_to_file = os.path.join(
            path_to_download_folder,
            [x for x in os.listdir(path_to_download_folder) if x[0] != '.'][0],
        )
        data = pd.read_excel(path_to_file)

        cat_with_kw = pd.read_csv(
            os.path.join('parser_app', 'logic', 'description', 'category_with_keywords.csv')
        )
        cat_titles = list(cat_with_kw['cat_title'])

        df, unit_dict = GKS_handler_interface.transform(data, cat_titles, 'msk')
        print('finish GKS transformation')

        print(f"local store shape : {self._local_store.shape}")
        print(f"appended df shape : {df.shape}")

        self._local_store = self._local_store.append(df, ignore_index=True)
        self._local_store.drop_duplicates(inplace=True)
        self._units_table = unit_dict
        self._save_local_store()

        # shutil.rmtree(path_to_download_folder)

    @staticmethod
    def transform(df: pd.DataFrame, cat_titles: List[str], city='msk') \
            -> Tuple[pd.DataFrame, Dict[str, Tuple[str, float]]]:
        """
        Columns - data range, category titles, ...
        Rows - prices

        :return
            pd.DataFrame with prices
            Dict[keys - string - category title, values - units - Tuple[units title, unit value]]
        """
        city = city.lower()
        assert city in ['msk', 'spb']

        dates = list(df.iloc[0])[2:]
        dates = [tuple(y for y in x.split(' ') if len(y) > 4) for x in dates]

        df_dict_list = {
            tuple(x):
                {'date_range_start': x[0], 'date_range_end': x[1]} if len(x) == 2
                else
                {}
            for x in dates
        }
        unit_dict = {}

        cur_category = None
        for index, row in df.iterrows():
            if index == 0:
                continue

            # case of new category
            if 'город' not in row[0].lower():
                category = ','.join(row[0].split(',')[:-1]) if len(row[0].split(',')) > 1 else row[0]
                unit_part = row[0].split(',')[-1] if len(row[0].split(',')) >= 2 else row[0]
                if category in cat_titles:
                    unit_title, unit_value, ok = _extract_units_from_string(unit_part)
                    if ok:
                        unit_dict[category] = (unit_title, unit_value)
                    else:
                        unit_dict[category] = ('шт', 1.0)
                    cur_category = category
                    continue
                # fixme log - error
                print(f"can't extract category from {row[0]}, try this : {category}")
                cur_category = None

            if cur_category is None:
                continue

            # case of new city with last category prices
            if (city == 'msk' and 'москва' in row[0].lower()) or \
                    (city == 'spb' and 'санкт-петербург' in row[0].lower()):
                for date, price in zip(dates, row[2:]):
                    if len(df_dict_list[tuple(date)]) == 0:
                        continue
                    df_dict_list[tuple(date)].update({cur_category: float(price)})

        df_tr = pd.DataFrame(
            columns=['date_range_start', 'date_range_end', *cat_titles],
            data=[x for _, x in df_dict_list.items() if len(x) > 2],
        )

        def to_date(x):
            return datetime.datetime.strptime(x, "%d.%m.%Y").date()

        df_tr['date_range_start'] = df_tr['date_range_start'].apply(to_date)
        df_tr['date_range_end'] = df_tr['date_range_end'].apply(to_date)

        return df_tr, unit_dict


class GKS_weekly_handler(GKS_handler_interface):

    def get_handler_name(self) -> str:
        return 'gks_weekly_handler'

    def _construct_url(self, start_date: Date, end_date: Optional[Date] = None) -> str:
        # Тип "за период"
        filter_0_0 = "-17018"

        # date range
        filter_1_0 = GKS_handler_interface._construct_filter_for_weekly_dates(start_date, end_date)

        # category to show
        filter_2_0 = "109543%2C109422%2C109423%2C109425%2C109517%2C109549%2C109427%2C109550%2C109428%2C109430%2C109518%2C109396%2C109397%2C109432%2C109435%2C109560%2C109561%2C109562%2C109563%2C109566%2C109444%2C109451%2C109577%2C109524%2C109402%2C109525%2C109526%2C109457%2C109459%2C109460%2C109463%2C109464%2C109466%2C109468%2C109469%2C109470%2C109471%2C109594%2C109595%2C109474%2C109597%2C109476%2C109726%2C110321%2C109530%2C217794%2C109744%2C109534%2C109652%2C109654%2C109781%2C109681%2C109688%2C109811%2C109692%2C109693%2C109816%2C109831%2C109715%2C109841%2C109842%2C109721%2C109723%2C109849%2C109854%2C110387%2C110389%2C109972%2C109900%2C109983%2C109901%2C109996%2C109418%2C110335%2C109944%2C109946%2C217805%2C110029%2C109947%2C110030%2C109948%2C110031%2C217787%2C110043%2C110045%2C110174%2C110175%2C110053%2C110057%2C110180%2C110181%2C110184%2C110185%2C109419%2C110077%2C110102%2C110225%2C110103%2C110226%2C217806%2C110254%2C110135%2C110259%2C110137%2C110138%2C110261%2C110264%2C110142%2C110346%2C110268%2C110281%2C110416"

        # cities
        filter_3_0 = "13200%2C13183"

        return fr"https://showdata.gks.ru/report/274422/?&filter_0_0={filter_0_0}&filter_1_0={filter_1_0}&filter_2_0={filter_2_0}&filter_3_0={filter_3_0}&rp_submit=t"

    def transform_date_for_data(self, date: Date) -> Date:
        return date - datetime.timedelta(days=7)
