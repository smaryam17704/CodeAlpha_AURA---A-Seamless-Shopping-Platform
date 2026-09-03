from django.conf import settings
from django.db import models


class Notification(models.Model):
    NOTIF_TYPES = [
        ('order_confirmed', 'Order Confirmed'),
        ('order_processing', 'Order Processing'),
        ('order_shipped', 'Order Shipped'),
        ('order_out_for_delivery', 'Out for Delivery'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('general', 'General'),
    ]

    STATUS_MESSAGE_MAP = {
        'confirmed': ('order_confirmed', 'Your order {number} has been confirmed.'),
        'processing': ('order_processing', 'Your order {number} is being processed.'),
        'shipped': ('order_shipped', 'Your order {number} has shipped.'),
        'out_for_delivery': ('order_out_for_delivery', 'Your order {number} is out for delivery.'),
        'delivered': ('order_delivered', 'Your order {number} has been delivered.'),
        'cancelled': ('order_cancelled', 'Your order {number} was cancelled.'),
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES, default='general')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.message}'

    @classmethod
    def create_for_order_status(cls, order, status):
        mapping = cls.STATUS_MESSAGE_MAP.get(status)
        if not mapping or not order.user_id:
            return None
        notif_type, template = mapping
        return cls.objects.create(
            user=order.user,
            notif_type=notif_type,
            message=template.format(number=order.order_number),
            link=f'/orders/{order.order_number}/',
        )
