import uuid
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.db import models


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=12, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    active = models.BooleanField(default=True)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid_for(self, subtotal):
        if not self.active:
            return False, 'This coupon is no longer active.'
        if self.expiry_date and self.expiry_date < date.today():
            return False, 'This coupon has expired.'
        if subtotal < self.minimum_order_amount:
            return False, f'This coupon requires a minimum order of ₹{self.minimum_order_amount:.2f}.'
        return True, ''

    def compute_discount(self, subtotal):
        valid, _ = self.is_valid_for(subtotal)
        if not valid:
            return Decimal('0.00')
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100')
        else:
            discount = self.discount_value
        return min(discount, subtotal)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=12, choices=PAYMENT_STATUS_CHOICES, default='pending')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Snapshot of shipping details at time of order (independent of Address model changing later)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    shipping_address_line1 = models.CharField(max_length=200)
    shipping_address_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='India')

    PAYMENT_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('card', 'Credit / Debit Card (simulated)'),
        ('upi', 'UPI (simulated)'),
    ]
    payment_method = models.CharField(max_length=40, choices=PAYMENT_CHOICES, default='cash_on_delivery')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'AURA-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    @property
    def full_shipping_address(self):
        parts = [self.shipping_address_line1]
        if self.shipping_address_line2:
            parts.append(self.shipping_address_line2)
        parts.append(f'{self.shipping_city}, {self.shipping_state} {self.shipping_postal_code}')
        parts.append(self.shipping_country)
        return ', '.join(parts)

    STATUS_STEPS = ['pending', 'confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered']

    @property
    def status_steps_display(self):
        labels = dict(self.STATUS_CHOICES)
        return [(step, labels.get(step, step)) for step in self.STATUS_STEPS]

    @property
    def status_step_index(self):
        try:
            return self.STATUS_STEPS.index(self.status)
        except ValueError:
            return -1


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True, related_name='order_items')
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')

    # Snapshot fields — preserved even if the product/variant changes or is deleted later
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=40, blank=True)
    variant_label = models.CharField(max_length=150, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity
