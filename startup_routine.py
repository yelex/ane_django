import pandas as pd
from parser_app.models import PricesRaw

class SnapshotManager():


    def __init__(self):
        self.last_succ_date = None # доделать