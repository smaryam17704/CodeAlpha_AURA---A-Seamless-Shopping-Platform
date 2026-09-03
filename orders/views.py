from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import Address
from store.models import Product, ProductVariant
from .forms import CheckoutForm
from .models import Order, OrderItem, Coupon


class CheckoutLine:
    """A uniform line item wrapper so both cart-checkout and Buy-Now share one code path."""

    def __init__(self, product, variant, quantity):
        self.product = product
        self.variant = variant
        self.quantity = quantity

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


class CheckoutTotals:
    def __init__(self, subtotal, discount, shipping_cost):
        self.subtotal = subtotal
        self.discount = discount
        self.shipping_cost = shipping_cost
        self.total = subtotal - discount + shipping_cost


def _get_cart_lines(cart):
    return [CheckoutLine(item.product, item.variant, item.quantity) for item in cart.items_qs]


def _get_buy_now_lines(request):
    data = request.session.get('buy_now')
    if not data:
        return None
    product = Product.objects.filter(pk=data.get('product_id'), is_active=True).first()
    if not product:
        return None
    variant = None
    if data.get('variant_id'):
        variant = ProductVariant.objects.filter(pk=data['variant_id'], product=product, is_active=True).first()
        if not variant:
            return None
    return [CheckoutLine(product, variant, data.get('quantity', 1))]


def _compute_totals(lines, coupon=None):
    subtotal = sum((l.line_total for l in lines), Decimal('0.00'))
    discount = Decimal('0.00')
    if coupon:
        discount = coupon.compute_discount(subtotal)
    payable = subtotal - discount
    shipping_cost = Decimal('0.00') if payable <= 0 else (
        Decimal('0.00') if payable >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
        else Decimal(str(settings.SHIPPING_FLAT_RATE))
    )
    return CheckoutTotals(subtotal, discount, shipping_cost)


@login_required
@require_POST
def buy_now(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1

    variant = None
    if product.has_variants:
        variant_id = request.POST.get('variant_id')
        if not variant_id:
            messages.error(request, 'Please select an option before buying.')
            return redirect(product.get_absolute_url())
        variant = ProductVariant.objects.filter(pk=variant_id, product=product, is_active=True).first()
        if not variant:
            messages.error(request, 'The selected option is not available.')
            return redirect(product.get_absolute_url())

    available = variant.stock_quantity if variant else product.stock_quantity
    if available <= 0:
        messages.error(request, 'This product is currently out of stock.')
        return redirect(product.get_absolute_url())
    if quantity > available:
        messages.error(request, f'Only {available} in stock.')
        return redirect(product.get_absolute_url())

    request.session['buy_now'] = {
        'product_id': product.id,
        'variant_id': variant.id if variant else None,
        'quantity': quantity,
    }
    return redirect(f"{reverse('orders:checkout')}?mode=buy_now")


@login_required
def checkout(request):
    is_buy_now = request.GET.get('mode') == 'buy_now'

    if is_buy_now:
        lines = _get_buy_now_lines(request)
        if not lines:
            messages.error(request, 'Your Buy Now selection has expired. Please try again.')
            return redirect('store:shop')
    else:
        cart = request.cart
        lines = _get_cart_lines(cart)
        if not lines:
            messages.info(request, 'Your cart is empty — add something before checking out.')
            return redirect('store:shop')

    stock_problems = [l for l in lines if l.exceeds_stock or l.available_stock == 0]
    if stock_problems:
        for l in stock_problems:
            messages.error(
                request,
                f'"{l.product.name}" only has {l.available_stock} in stock. Please update your selection.'
            )
        return redirect('store:shop' if is_buy_now else 'cart:cart_detail')

    default_address = Address.objects.filter(user=request.user, is_default=True).first()
    initial = {
        'full_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
    }
    if default_address:
        initial.update({
            'phone_number': default_address.phone_number,
            'address_line1': default_address.address_line1,
            'address_line2': default_address.address_line2,
            'city': default_address.city,
            'state': default_address.state,
            'postal_code': default_address.postal_code,
            'country': default_address.country,
        })

    if request.method == 'POST':
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            order = _place_order(request, form, lines, is_buy_now)
            if order is not None:
                return redirect('orders:order_confirmation', order_number=order.order_number)
            return redirect('store:shop' if is_buy_now else 'cart:cart_detail')
    else:
        form = CheckoutForm(initial=initial)

    addresses = Address.objects.filter(user=request.user)
    totals = _compute_totals(lines)

    context = {
        'form': form,
        'cart': totals,
        'items': lines,
        'addresses': addresses,
        'is_buy_now': is_buy_now,
    }
    return render(request, 'orders/checkout.html', context)


def _place_order(request, form, lines, is_buy_now):
    """
    Executes the full order-creation integrity sequence atomically:
    validate -> recalc prices server-side -> apply coupon -> create order ->
    create items -> reduce stock -> clear cart/buy-now session -> notify.
    """
    cd = form.cleaned_data

    coupon = None
    if cd.get('coupon_code'):
        coupon = Coupon.objects.filter(code=cd['coupon_code'].strip().upper()).first()
        if not coupon:
            messages.error(request, 'That coupon code is not valid.')
            return None

    with transaction.atomic():
        locked_lines = []
        for line in lines:
            product = Product.objects.select_for_update().get(pk=line.product.pk)
            variant = None
            if line.variant:
                variant = ProductVariant.objects.select_for_update().get(pk=line.variant.pk)
            available = variant.stock_quantity if variant else product.stock_quantity
            if line.quantity > available:
                messages.error(
                    request,
                    f'"{product.name}" no longer has enough stock ({available} left). Please adjust your selection.'
                )
                return None
            locked_lines.append((product, variant, line.quantity))

        subtotal = sum((
            (v.effective_price if v else p.price) * qty for p, v, qty in locked_lines
        ), Decimal('0.00'))

        discount = Decimal('0.00')
        if coupon:
            valid, err = coupon.is_valid_for(subtotal)
            if not valid:
                messages.error(request, err)
                return None
            discount = coupon.compute_discount(subtotal)

        payable = subtotal - discount
        shipping_cost = Decimal('0.00') if payable <= 0 else (
            Decimal('0.00') if payable >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
            else Decimal(str(settings.SHIPPING_FLAT_RATE))
        )
        total = payable + shipping_cost

        payment_status = 'paid' if cd['payment_method'] in ('card', 'upi') else 'pending'

        order = Order.objects.create(
            user=request.user,
            full_name=cd['full_name'],
            email=cd['email'],
            phone_number=cd['phone_number'],
            shipping_address_line1=cd['address_line1'],
            shipping_address_line2=cd.get('address_line2', ''),
            shipping_city=cd['city'],
            shipping_state=cd['state'],
            shipping_postal_code=cd['postal_code'],
            shipping_country=cd['country'],
            payment_method=cd['payment_method'],
            payment_status=payment_status,
            coupon=coupon,
            subtotal=subtotal,
            discount=discount,
            shipping_cost=shipping_cost,
            total=total,
            status='confirmed',
        )

        for product, variant, qty in locked_lines:
            unit_price = variant.effective_price if variant else product.price
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                product_name=product.name,
                product_sku=(variant.sku if variant else product.sku),
                variant_label=(variant.label if variant else ''),
                unit_price=unit_price,
                quantity=qty,
            )
            if variant:
                variant.stock_quantity -= qty
                variant.save(update_fields=['stock_quantity'])
            else:
                product.stock_quantity -= qty
                product.save(update_fields=['stock_quantity'])

        if cd.get('save_address'):
            Address.objects.create(
                user=request.user,
                full_name=cd['full_name'],
                phone_number=cd['phone_number'],
                address_line1=cd['address_line1'],
                address_line2=cd.get('address_line2', ''),
                city=cd['city'],
                state=cd['state'],
                postal_code=cd['postal_code'],
                country=cd['country'],
                is_default=not Address.objects.filter(user=request.user).exists(),
            )

        if is_buy_now:
            request.session.pop('buy_now', None)
        else:
            request.cart.items.all().delete()

    from notifications.models import Notification
    Notification.create_for_order_status(order, 'confirmed')

    messages.success(request, f'Order {order.order_number} placed successfully!')
    return order


@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
