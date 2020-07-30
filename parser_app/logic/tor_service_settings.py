import json
import os

from anehome.settings import DEVELOP_MODE
from anehome.utils import get_os_short_name


# for OSX '9150' is default
# for Linux '9050' is default
# for Windows use google
TOR_SERVICE_PORT = '9050'
TOR_SERVICE_HOST = '127.0.0.1'

if os.path.exists(os.path.join('parser_app', 'logic', 'tor_service_default_port.json')):
    print("Try to use Tor Service port defined in 'tor_service_default_port.json'")
    try:
        TOR_SERVICE_PORT = json.load(open(
            os.path.join('parser_app', 'logic', 'tor_service_default_port.json'),
            'r'
        ))['port']
    except:
        print(f"Error while loading Tor Service port from 'tor_service_default_port.json")
        print(f"Use port : {TOR_SERVICE_PORT}")
else:
    os_short_name = get_os_short_name()
    if os_short_name == 'linux':
        TOR_SERVICE_PORT = '9050'
    elif os_short_name == 'mac':
        TOR_SERVICE_PORT = '9150'
    else:
        print('You use some strange OS')

if DEVELOP_MODE:
    TOR_SERVICE_PORT = '9050'

print(f"For Tor Service will be used port {TOR_SERVICE_PORT},\n"
      f"if you another port, please create in 'logic' folder file with name 'tor_service_default_port.json'"
      "and place there '{\"port\": \"<YOUR PORT>\"}' where <YOUR PORT> is your Tor Service port.")
