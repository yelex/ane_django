import re
import time

import pandas as pd
from typing import Dict, Union, List, Optional, Tuple

ParsedProduct = Dict[str, Union[str, float, None]]


def get_empty_parsed_product_dict() -> ParsedProduct:
    """
    Just create ParsedProduct empty item. It is just dict with a specific fields.
    See comments inside this functions.

    :return: empty ParsedProduct
    """
    return {
        # string, title from shop site
        'title': None,

        # string, url to product
        'url': None,

        # float, value in unit of unit_title
        'unit_value': None,

        # string, name of units
        'unit_title': None,

        # string, unparsed units
        'unparsed_units': None,

        # float, current price
        'price_new': None,

        # float, not none if offer detected and old price is available
        'price_old': None,
    }


def load_page_with_TL(web_driver, page_url, time_limit: float = 5) -> Union[str, None]:
    """
    Helper function. Load url with tl. Then tl is reached returned loaded page.
    :param web_driver: selenium web driver
    :param page_url: string, url to load
    :param time_limit: float, time to wait
    :return: str, page source
    """
    try:
        web_driver.set_page_load_timeout(time_limit)
        web_driver.get(page_url)
        time.sleep(time_limit)
        page_source = web_driver.page_source
        if len(page_source) < 300:
            return None
        return page_source
    except:
        try:
            web_driver.execute_script("window.stop();")
            page_source = web_driver.page_source
            if len(page_source) < 300:
                return None
            return page_source
        except:
            return None


def validate_ParsedProduct(parsed_product: ParsedProduct):
    """
    Function used by handler interface class to validate items returned from parsers implementations.

    :param parsed_product:
    :return: None, but can raise assert if something went wrong with data formats.
    """
    assert isinstance(parsed_product, dict), "ParsedProduct must be dist"

    for key in ['title', 'url', 'unit_value', 'unit_title', 'unparsed_units', 'price_new', 'price_old']:
        assert key in parsed_product.keys(), \
            f"ParsedProduct must have this filed : {key}\n"\
            f"and you have {parsed_product}"

    for not_nan_key in ['title', 'url', 'price_new']:
        assert parsed_product[not_nan_key] is not None, \
            f"ParsedProduct must have this filed as non None : {not_nan_key}"\
            f"and you have {parsed_product}"

    assert type(parsed_product['title']) == str
    assert type(parsed_product['url']) == str
    assert type(parsed_product['price_new']) == float
    assert type(parsed_product['price_old']) == float or parsed_product['price_old'] is None


def postprocess_parsed_product(parsed_product: ParsedProduct, category_row) -> ParsedProduct:
    """
    Make some preparations with row ParsedProduct.
    Lowercase title. Remove double spaces. Extract units from product description.

    :param category_row:
    :param parsed_product: ParsedProduct from handlers, function assume that this parsed_product
        pass validate_ParsedProduct tests.
    :return: ParsedProduct with ready to use
    """

    # title to loser case
    parsed_product['title'] = remove_odd_space(parsed_product['title'].lower())
    # remove quotes
    if parsed_product['title'][0] in {'"', "'"}:
        parsed_product['title'] = parsed_product['title'][1:]
    if parsed_product['title'][-1] in {'"', "'"}:
        parsed_product['title'] = parsed_product['title'][:-1]

    if isinstance(parsed_product['price_new'], str):
        parsed_product['price_new'] = float(remove_ALL_spaces(parsed_product['price_new']).lower().replace(',', '.'))

    # set unit title
    parsed_product = extract_units_from_parsed_product(parsed_product, category_row)

    return parsed_product


def get_empty_handler_DF() -> pd.DataFrame:
    """
    Create dataframe with preseted columns, this df will be used in extract_product function
    :return: pd.DataFrame
    """
    df = pd.DataFrame(columns=['date', 'type', 'category_id', 'category_title',
                               'site_title', 'price_new', 'price_old', 'site_unit',
                               'site_link', 'site_code', 'miss'])
    return df


def remove_odd_space(x: str) -> str:
    """
    Remove multiple spaces, remove quites, remove firts and last spaces if them exist

    :param x: string to process:
    :return: processed string
    """
    assert isinstance(x, str), f"x must be string, but you pass {type(x)}"
    _x = re.sub(r'"', " ", x)
    _x = re.sub(r"'", " ", x)
    _x = re.sub(r'\n', " ", x)
    _x = _x.replace(u'\xa0', ' ')
    _x = re.sub(r"\s\s+", " ", _x)
    if len(x) > 0 and _x[0] == ' ':
        _x = _x[1:]
    if len(x) > 0 and _x[-1] == ' ':
        _x = _x[:-1]
    return str(_x)


def remove_non_digits(x: str) -> str:
    """
    Remove all non digits symbols from string

    :param x: string to process:
    :return: processed string
    """
    assert isinstance(x, str), f"x must be string, but you pass {type(x)}"
    return re.sub(r'\D', '', x)


def remove_ALL_spaces(x: str) -> str:
    """
    Remove all spaces from string

    :param x: string to process:
    :return: processed string
    """
    assert isinstance(x, str), f"x must be string, but you pass {type(x)}"
    _x = remove_odd_space(x)
    _x = _x.replace(' ', '')
    return str(_x)


def extract_units_from_parsed_product(parsed_product: ParsedProduct, category_row: Optional[dict] = None) -> ParsedProduct:
    """
    Extract units from parsed_product. Firstly look at field

    :param parsed_product: ParsedProduct to extract units from
    :param category_row: optional parameter, if not None used for more accurate unit prediction
    :return: ParsedProduct same as input one, but with filled units fields
    """
    assert isinstance(parsed_product, dict), f"Parsed product must be dict, and you have {type(parsed_product)}"
    unit_sources = []

    if parsed_product['unparsed_units'] is not None:
        parsed_product['unparsed_units'] = remove_ALL_spaces(parsed_product['unparsed_units'].lower())
        unit_sources.append(parsed_product['unparsed_units'])

    if parsed_product['title'] is not None:
        unit_sources.append(parsed_product['title'])

    for unit_string in unit_sources:
        unit_name, unit_value, success = _extract_units_from_string(unit_string)

        if success:
            parsed_product['unit_value'] = unit_value
            parsed_product['unit_title'] = unit_name
            break

    if parsed_product['unit_value'] is None:
        if category_row is not None:
            parsed_product['unit_value'] = category_row['default_unit_value']
            parsed_product['unit_title'] = category_row['default_unit_title']
        else:
            parsed_product['unit_value'] = 1
            parsed_product['unit_title'] = 'кг'

    return parsed_product


def _extract_units_from_string(unit_string) -> Tuple[str, float, bool]:
    """
    Extract units from string.

    :param unit_string: string to extract units
    :return: tuple of three items: <extracted unit title, extracted value, success of extraction>
        if success if false, first ans second returned value should be ignored
    """
    # single number : 12 or 1.4
    re_single_number = r"\d+\.\d+|\d+"

    # range of numbers 1-2 or 1.5-1.6 or 1-1.1
    re_number_range = rf"({re_single_number})-({re_single_number})"

    # single number or number range
    re_number = rf"{re_number_range}|{re_single_number}"

    # regular expression for units
    re_mass_units = r"кг|г"
    re_value_units = r"мл|л"
    re_cnt_units = r"шт"
    re_unit = rf"{re_mass_units}|{re_value_units}|{re_cnt_units}"

    match = re.search(rf"({re_number})\s*({re_unit})", unit_string.replace(',', '.'))

    if match is None:
        return _search_for_only_unit_title(unit_string)

    if not hasattr(match, 'groups') or len(match.groups()) != 4:
        return "error no group", 0.0, False

    title_string = match.groups()[-1]

    # case of single number
    if (match.groups()[1] is None) and (match.groups()[2] is None):
        value = float(match.groups()[0])
    elif (match.groups()[1] is not None) and (match.groups()[2] is not None):
        value = (float(match.groups()[1]) + float(match.groups()[2])) / 2
    else:
        return "no match in group", 0.0, False

    return title_string, value, True


def _search_for_only_unit_title(unit_string: str) -> Tuple[str, float, bool]:
    # regular expression for units
    re_mass_units = r"кг|г"
    re_value_units = r"мл|л"
    re_cnt_units = r"шт"
    re_unit = rf"{re_mass_units}|{re_value_units}|{re_cnt_units}"

    match = re.search(rf"({re_unit})", unit_string.replace(',', '.'))

    if match is None:
        return "error no match", 0.0, False

    if not hasattr(match, 'groups') or len(match.groups()) != 1:
        return "error no group", 0.0, False

    return match.group(0), 1.0, True
