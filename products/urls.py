from django.urls import path
from products.views import get_product, move_to_cart

urlpatterns = [
    path('move_to_cart/<uid>/', move_to_cart, name='move_to_cart'),
    path('<slug>/', get_product, name='get_product'),
]
