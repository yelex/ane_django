"""
This file represents some utils to operate with path in OS dependent way
"""
import sys
import os
from typing import Tuple

WIN_HOME_DIR = r'D:\ANE_2'


def get_path_prefix() -> str:
    if sys.platform.startswith('linux'):
        # return relative for Linux, it probably will be root of Django project
        return '.'
    elif sys.platform.contain('win'):
        return WIN_HOME_DIR
    else:
        raise ValueError("You OS wasn't found, please add it to 'anehome/path_utils.py'")


def OS_dep_path_join(*args) -> str:
    return os.path.join(get_path_prefix(), *args)
