from os.path import dirname, join, realpath, exists
from os import makedirs

from parser_app.logic.handlers.handler_tools import load_page_with_TL
from parser_app.logic.proxy_tools.common_proxy_testers import test_html_page
from parser_app.logic.global_status import \
    create_tor_webdriver, \
    create_tor_service_browser


def main():
    out_img_folder = join(dirname(realpath(__file__)), "tor_test_screenshots")
    if not exists(out_img_folder):
        makedirs(out_img_folder)

    # print('creating TorDriver... ', end='')
    # driver = create_tor_webdriver()
    # DRIVER_TYPE = 'TOR'
    # print('ok')

    print('creating Chrome driver with tor service proxy... ', end='')
    driver = create_tor_service_browser()
    DRIVER_TYPE = 'CHROME'
    print('ok')

    print('Start iterating over test pages...\n')
    for (site_url, site_name) in [
        ('https://check.torproject.org', 'tor_check'),
        ('https://www.eldorado.ru', 'eldorado'),
        ('https://www.ikea.com/ru/ru/', 'ikea'),
        ('https://lenta.com/', 'lenta'),
        ('https://www.okeydostavka.ru/spb', 'okey'),
        ('https://www.perekrestok.ru/', 'perekrestok'),
        ('https://rigla.ru/', 'rigla'),
        ('https://www.svyaznoy.ru', 'svaznoy'),
    ]:
        print(f'Check {site_name}:')
        try:
            page_source = None
            if DRIVER_TYPE == 'TOR':
                print(f'loading... ', end='')
                driver.load_url(site_url, wait_for_page_body=True)
                page_source = driver.page_source
                print('ok')
            elif DRIVER_TYPE == 'CHROME':
                MAX_WAIT_TIME_S = 3.0
                print(f'loading (max wait time {MAX_WAIT_TIME_S}s)... ', end='')
                page_source = load_page_with_TL(driver, site_url, MAX_WAIT_TIME_S)
                print('ok')

            print('make screen-shot... ', end='')
            driver.get_screenshot_as_file(join(out_img_folder, site_name + '.png'))
            print('ok')

            if not test_html_page(page_source):
                print(f'{site_name} FAIL')
            else:
                print(f'{site_name} OK')
            print()

        except:
            print(f'Error while loading {site_name}')

    print('quiting driver... ', end='')
    driver.quit()
    print('ok')

    print('Please, look at screen-shots of these sites, them are in `tor_test_screenshots` folder.')


if __name__ == "__main__":
    main()
