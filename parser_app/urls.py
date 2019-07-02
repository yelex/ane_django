from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('getNewSnap/', views.get_snap, name='getSnap'),
    path('cp/', views.cp, name='cp')
]
