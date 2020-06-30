from tbselenium.tbdriver import TorBrowserDriver
from os.path import dirname, join, realpath, getsize


def main():
    out_img = join(dirname(realpath(__file__)), "tor_test_screenshot.png")
    # with TorBrowserDriver("../tor-browser-linux64-9.5_en-US/tor-browser_en-US/") as driver:
    #     driver.load_url('https://check.torproject.org', wait_for_page_body=True)
    #     print("----" * 10)
    #     driver.get_screenshot_as_file(out_img)
    #     print("----" * 10)
    # print("Screenshot is saved as %s (%s bytes)" % (out_img, getsize(out_img)))

    print("1 / 5")
    driver = TorBrowserDriver(
        "../tor-browser-linux64-9.5_en-US/tor-browser_en-US",
    )
    print("2 / 5")
    # driver.load_url('https://check.torproject.org', wait_for_page_body=True)
    # driver.load_url('https://www.svyaznoy.ru/search?q=радио', wait_for_page_body=True) # -
    # driver.load_url("https://lenta.com/", wait_for_page_body=True) # -
    # driver.load_url("https://www.ikea.com/ru/ru/", wait_for_page_body=True) # +
    # driver.load_url("https://www.perekrestok.ru/", wait_for_page_body=True) # +
    driver.load_url("https://rigla.ru/", wait_for_page_body=True) # +
    print("3 / 5")
    driver.get_screenshot_as_file(out_img)
    print("4 / 5")
    driver.quit()
    print("5 / 5")


if __name__ == "__main__":
    main()
