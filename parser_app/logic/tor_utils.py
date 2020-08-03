# some code taken from https://python-scripts.com/question/10246

from urllib.error import URLError
from urllib.request import urlopen

from subprocess import check_call, CalledProcessError, getoutput
from json import load
from os import devnull
import time
from stem import Signal
from stem.control import Controller
# import socks
# import socket

from parser_app.logic.tor_service_settings import TOR_SERVICE_PORT, TOR_SERVICE_PASSWORD, TOR_SERVICE_HOST


def colored(r, g, b, text):
    return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(r, g, b, text)


def renew_tor_service_ip():
    print(f"{colored(10, 250, 10, 'TOR-SERVICE')} take new ip")
    try:
        with Controller.from_port(address=TOR_SERVICE_HOST, port=int(TOR_SERVICE_PORT)) as controller:
            controller.authenticate(password=TOR_SERVICE_PASSWORD)
            # socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, TOR_SERVICE_HOST, TOR_SERVICE_PORT)
            # socket.socket = socks.socksocket
            controller.signal(Signal.NEWNYM)

        time.sleep(5)
    except:
        print(f"{colored(250, 10, 10, 'TOR-SERVICE')} fail, smth went wrong")


def restart_tor_LINUX():
    """
    require SUDO
    :return:
    """
    fnull = open(devnull, 'w')
    try:
        tor_restart = check_call(
            ["service", "tor", "restart"],
            stdout=fnull,
            stderr=fnull,
        )

        if tor_restart is 0:
            print(" {0}".format(
                "[\033[92m+\033[0m] Anonymizer status \033[92m[ON]\033[0m"))
            print(" {0}".format(
                "[\033[92m*\033[0m] Getting public IP, please wait..."))
            retries = 0
            my_public_ip = None
            while retries < 12 and not my_public_ip:
                retries += 1
                try:
                    my_public_ip = load(urlopen('http://jsonip.com/'))['ip']
                except URLError:
                    time.sleep(5)
                    print(" [\033[93m?\033[0m] Still waiting for IP address...")
            print()
            if not my_public_ip:
                my_public_ip = getoutput('wget -qO - v4.ifconfig.co')
            if not my_public_ip:
                exit(" \033[91m[!]\033[0m Can't get public ip address!")
            print(" {0}".format("[\033[92m+\033[0m] Your IP is \033[92m%s\033[0m" % my_public_ip))
    except CalledProcessError as err:
        print("\033[91m[!] Command failed: %s\033[0m" % ' '.join(err.cmd))

