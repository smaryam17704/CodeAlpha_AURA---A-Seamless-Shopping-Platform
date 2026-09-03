from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_sku', 'variant_label', 'unit_price', 'quantity')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'discount', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'email')
    readonly_fields = ('order_number', 'subtotal', 'shipping_cost', 'total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    list_editable = ('status', 'payment_status')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        status_changed = change and 'status' in form.changed_data
        previous_status = None
        if status_changed:
            previous_status = Order.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)
        if status_changed and obj.user_id:
            from notifications.models import Notification
            Notification.create_for_order_status(obj, obj.status)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'minimum_order_amount', 'active', 'expiry_date')
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)
