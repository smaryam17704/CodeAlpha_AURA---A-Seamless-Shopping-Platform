from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('', views.order_history, name='order_history'),
    path('<str:order_number>/', views.order_detail, name='order_detail'),
]
