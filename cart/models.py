from decimal import Decimal
from django.conf import settings
from django.db import models


class Cart(models.Model):
    """A cart belongs either to an authenticated user OR to a guest session key, never both."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        owner = self.user.username if self.user else f'guest:{self.session_key}'
        return f'Cart({owner})'

    @property
    def items_qs(self):
        return self.items.select_related('product', 'product__category').all()

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items_qs)

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items_qs), Decimal('0.00'))

    @property
    def shipping_cost(self):
        if self.subtotal == 0:
            return Decimal('0.00')
        if self.subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD)):
            return Decimal('0.00')
        return Decimal(str(settings.SHIPPING_FLAT_RATE))

    @property
    def total(self):
        return self.subtotal + self.shipping_cost


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'variant')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.quantity} x {self.product.name}' + (f' ({self.variant.label})' if self.variant else '')

    @property
    def unit_price(self):
        return self.variant.effective_price if self.variant else self.product.price

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def available_stock(self):
        return self.variant.stock_quantity if self.variant else self.product.stock_quantity

    @property
    def exceeds_stock(self):
        return self.quantity > self.available_stock
