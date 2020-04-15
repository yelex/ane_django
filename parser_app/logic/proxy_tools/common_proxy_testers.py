import os

from selenium import webdriver
import json

from parser_app.logic.global_status import create_webdriver_with_proxy


GOOGLE_CHROME_ERROR_LIST = json.load(
    open(os.path.join('.', 'parser_app', 'logic', 'proxy_tools', 'google_chrome_error_list.json'))
)


def simple_test_is_proxy_suit(proxy_ip_with_port: str, site_handler) -> bool:
    """
    test proxy for suilt site_handler test url

    :param proxy_ip_with_port: str
    :param site_handler: HandlerInterface
    :return:
    """
    driver = create_webdriver_with_proxy(proxy_ip_with_port)
    return simple_test_driver_with_url(driver, site_handler.get_test_ulr())


def simple_test_driver_with_url(driver: webdriver.Chrome, url: str) -> bool:
    try:
        driver.get(url)
        page = driver.page_source
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

