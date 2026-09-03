from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    path('journal/', views.journal, name='journal'),
    path('contact/', views.contact, name='contact'),
]
