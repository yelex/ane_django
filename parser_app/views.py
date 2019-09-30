from django.shortcuts import render
from parser_app.logic.total import Total
from parser_app.models import PricesRaw
import pandas as pd
import django_tables2 as tables
from startup_routine import SnapshotManager
import numpy as np
from datetime import datetime, timedelta
# from startup_routine import


class PriceTable(tables.Table):
    index = tables.Column(verbose_name='ID категории')
    type = tables.Column(verbose_name='Тип')
    category_title = tables.Column(verbose_name='Категория')
    globus = tables.Column(verbose_name='Глобус (цена)')
    okey = tables.Column(verbose_name='Окей (цена)')
    perekrestok = tables.Column(verbose_name='Перекресток (цена)')
    utkonos = tables.Column(verbose_name='Утконос (цена)')
    lamoda = tables.Column(verbose_name='Ламода (цена)')
    ozon = tables.Column(verbose_name='Озон (цена)')
    piluli = tables.Column(verbose_name='Piluli (цена)')
    mvideo = tables.Column(verbose_name='м.Видео (цена)')
    services = tables.Column(verbose_name='Услуги (цена)')


def index(request):

    fresh_snapshot_date = SnapshotManager().last_succ_date
    print(fresh_snapshot_date)
    df = pd.DataFrame(list(PricesRaw.objects.filter(date=PricesRaw.objects.last().date).all().values()))
    print(df.head())
    df.date = pd.to_datetime(df.date)
    pivot = df.pivot_table(index=['type', 'category_title'],
                           columns='site_code', values='price_new', aggfunc=lambda x: round(x.mean(), 2)).reset_index()
    # print(pivot.reset_index().columns)
    pivot = pivot.reset_index()#[['index', 'type', 'category_title', 'globus',
                                # 'okey', 'perekrestok', 'utkonos', 'lamoda', 'ozon',
                               #  'piluli', 'mvideo', 'services']]
    return render(request, 'parser_app/index.html', {'snapstable': PriceTable(pivot.to_dict('records')), # добавить ,
                                                     'last_succ_snap_date' : fresh_snapshot_date})


def get_snap(request):
    Total().get_new_snap_threaded()
    return render(request, 'parser_app/cp.html', {})


def cp(request):
    if request.method == 'GET':
        return render(request, 'parser_app/cp.html', {})

def snaps(request):
    if request.method == 'GET':
        return render(request, 'parser_app/cp.html', {})
# Create your views here.
