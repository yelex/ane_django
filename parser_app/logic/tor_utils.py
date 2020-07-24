# code taken from https://python-scripts.com/question/10246

from urllib.error import URLError
from urllib.request import urlopen

from subprocess import check_call, CalledProcessError, getoutput
from json import load
from os import devnull
import time


def restart_tor():
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

