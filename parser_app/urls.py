from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^\w*/getNewSnap$', views.get_snap, name='getSnap'),
    path('cp/', views.cp, name='cp'),
    path('dynamics/', views.dynamics, name='dynamics'),
    path('snaps/', views.snaps, name='snaps')
]
# path('getNewSnap/', views.get_snap, name='getSnap'),
