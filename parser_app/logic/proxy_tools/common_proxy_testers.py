import os

from selenium import webdriver
import json

from parser_app.logic.global_status import create_webdriver_with_proxy
from parser_app.logic.handlers.handler_tools import load_page_with_TL


GOOGLE_CHROME_ERROR_LIST = json.load(
    open(os.path.join('.', 'parser_app', 'logic', 'proxy_tools', 'google_chrome_error_list.json'))
)


def simple_test_driver_with_url(driver: webdriver.Chrome, url: str) -> bool:
    try:
        page = load_page_with_TL(driver, url, 7.5)
        if page is None:
            return False
        if len(page) < 500:
            return False
        page_text = str(page).lower()
    except:
        return False

    if "no internet" in page_text:
        return False

    if "bad ip" in page_text:
        return False

    for google_chrome_error in GOOGLE_CHROME_ERROR_LIST:
        if google_chrome_error.lower() in page_text:
            return False

    return True

