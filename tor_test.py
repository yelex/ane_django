from os.path import dirname, join, realpath, exists
from os import makedirs

from parser_app.logic.global_status import create_tor_webdriver


def main():
    out_img_folder = join(dirname(realpath(__file__)), "tor_test_screenshots")
    if not exists(out_img_folder):
        makedirs(out_img_folder)

    print('creating TorDriver... ', end='')
    driver = create_tor_webdriver()
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
            print(f'loading... ', end='')
            driver.load_url(site_url, wait_for_page_body=True)
            print('ok')

            print('make screen-shot... ', end='')
            driver.get_screenshot_as_file(join(out_img_folder, site_name + '.png'))
            print('ok')

            if isinstance(driver.page_source, str):
                content_len = len(driver.page_source)
                content = driver.page_source
            else:
                content_len = 0
                content = ""
            print(f'content len is {content_len}')

            if content_len < 500 or "an error occurred" in content.lower():
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
