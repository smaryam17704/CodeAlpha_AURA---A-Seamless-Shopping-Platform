from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.AuraLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_dashboard, name='account_dashboard'),
    path('account/profile/', views.profile_edit, name='profile_edit'),
    path('account/preferences/', views.preferences, name='preferences'),
    path('account/addresses/', views.address_list, name='address_list'),
    path('account/addresses/add/', views.address_create, name='address_create'),
    path('account/addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('account/addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
]
