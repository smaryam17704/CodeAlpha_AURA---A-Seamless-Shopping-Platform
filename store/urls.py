from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('shop/', views.shop, name='shop'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('quick-view/<int:product_id>/', views.quick_view, name='quick_view'),
    path('shop/<slug:slug>/', views.product_detail, name='product_detail'),
]
