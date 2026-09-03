from django.contrib import admin
from .models import Address, Profile


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'address_type', 'is_default')
    list_filter = ('address_type', 'is_default', 'state')
    search_fields = ('user__username', 'full_name', 'city')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'theme_preference', 'newsletter_opt_in', 'order_update_emails', 'created_at')
    list_filter = ('theme_preference', 'newsletter_opt_in', 'order_update_emails')
    search_fields = ('user__username', 'user__email', 'phone_number')
