import os

from selenium import webdriver
import json

from parser_app.logic.global_status import create_webdriver_with_proxy
from parser_app.logic.handlers.handler_tools import load_page_with_TL

GOOGLE_CHROME_ERROR_LIST = json.load(
    open(os.path.join('.', 'parser_app', 'logic', 'proxy_tools', 'google_chrome_error_list.json'))
)


# def simple_test_is_proxy_suit(proxy_ip_with_port: str, site_handler) -> bool:
#     """
#     test proxy for suilt site_handler test url
#
#     :param proxy_ip_with_port: str
#     :param site_handler: HandlerInterface
#     :return:
#     """
#     try:
#         driver = create_webdriver_with_proxy(proxy_ip_with_port)
#         test_result = simple_test_driver_with_url(driver, site_handler.get_test_ulr())
#         return test_result
#     except:
#         return False
#     finally:
#         try:
#             driver.quit()
#         except:
#             pass


def simple_test_driver_with_url(driver: webdriver.Chrome, url: str) -> bool:
    try:
        page = load_page_with_TL(driver, url, 7.5)
        if page is None:
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

