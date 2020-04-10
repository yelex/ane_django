from django.urls import path, re_path
from . import views
from parser_app.logic.global_status import Global

urlpatterns = [
    path('', views.home, name='home'),
    path('mean_prices/', views.mean_prices, name='mean_prices'),
    re_path(r'^\w*/getNewSnap$', views.get_snap, name='getSnap'),
    path('cp/', views.cp, name='cp'),
    path('dynamics/', views.dynamics, name='dynamics'),
    path('snaps/', views.snaps, name='snaps')
]

# Global().getproxies()
# path('getNewSnap/', views.get_snap, name='getSnap'),
