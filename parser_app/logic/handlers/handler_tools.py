import time

import pandas as pd
from typing import Dict, Union, List

from bs4 import BeautifulSoup
import numpy as np
from selenium import webdriver

from parser_app.logic.global_status import Global
from parser_app.logic.handlers.tools import remove_odd_space

ParsedProduct = Dict[str, Union[str, float, None]]


def get_empty_parsed_product_dict() -> ParsedProduct:
    return {
        # string, title from shop site
        'title': None,

        # string, url to product
        'url': None,

        # float, value in unit of unit_title
        'unit_value': None,

        # string, name of units
        'unit_title': None,

        # float, current price
        'price_new': None,

        # float, not none if offer detected and old price is available
        'price_old': None,
    }


def validate_ParsedProduct(parsed_product: ParsedProduct):
    assert isinstance(parsed_product, dict), "ParsedProduct must be dist"

    for key in ['title', 'url', 'unit_value', 'unit_title', 'price_new', 'price_old']:
        assert key in parsed_product.keys(), f"ParsedProduct must have this filed : {key}\n"\
                                             f"and you have {parsed_product}"

    for not_nan_key in ['title', 'url', 'price_new']:
        assert parsed_product[not_nan_key] is not None, \
            f"ParsedProduct must have this filed as non None : {not_nan_key}"\
            f"and you have {parsed_product}"

    assert type(parsed_product['title']) == str
    assert type(parsed_product['url']) == str
    assert type(parsed_product['price_new']) == float
    assert type(parsed_product['price_old']) == float or parsed_product['price_old'] is None


def postprocess_parsed_product(parsed_product: ParsedProduct) -> ParsedProduct:
    validate_ParsedProduct(parsed_product)

    # title to loser case
    parsed_product['title'] = remove_odd_space(parsed_product['title'].lower())

    # set unit title
    if parsed_product['unit_title'] is not None:
        parsed_product['unit_title'] = remove_odd_space(parsed_product['unit_title'].lower())


    if parsed_product['unit_title'] is None:


    return parsed_product


def get_empty_handler_DF() -> pd.DataFrame:
    """
    Create dataframe with preseted columns, this df will be used in extract_product function
    :return: pd.DataFrame
    """
    df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                               'site_title', 'price_new', 'price_old', 'site_unit',
                               'site_link', 'site_code'])
    return df
