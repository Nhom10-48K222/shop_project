from django.urls import path
from home.views import *

urlpatterns = [
    path('', home, name="home"),
    path('index/', index, name="index"),
    path('search/', product_search, name='product_search'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('terms-and-conditions/', terms_and_conditions, name='terms-and-conditions'),
    path('privacy-policy/', privacy_policy, name='privacy-policy'),
    path('article_detail/', article_detail, name='article_detail'),
]
