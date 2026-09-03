from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse

from store.models import Product, ProductVariant
from .models import CartItem


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _resolve_variant(product, variant_id):
    """Returns (variant, error_message). variant is None if product has no variants."""
    if not product.has_variants:
        return None, None
    if not variant_id:
        return None, 'Please select an option before adding to cart.'
    variant = ProductVariant.objects.filter(pk=variant_id, product=product, is_active=True).first()
    if not variant:
        return None, 'The selected option is not available.'
    return variant, None


@require_GET
def cart_detail(request):
    cart = request.cart
    items = cart.items_qs
    return render(request, 'cart/cart.html', {'cart': cart, 'items': items})


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = request.cart

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, quantity)

    variant, error = _resolve_variant(product, request.POST.get('variant_id'))
    if error:
        if _is_ajax(request):
            return JsonResponse({'success': False, 'message': error}, status=400)
        messages.error(request, error)
        return redirect(product.get_absolute_url())

    available_stock = variant.stock_quantity if variant else product.stock_quantity
    if available_stock <= 0:
        msg = 'This product is currently out of stock.'
        if _is_ajax(request):
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(product.get_absolute_url())

    item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity

    stock_msg = None
    if item.quantity > available_stock:
        item.quantity = available_stock
        stock_msg = f'Only {available_stock} left — quantity adjusted to available stock.'
    item.save()

    label = f'{product.name} ({variant.label})' if variant else product.name
    msg = f'Added "{label}" to your cart.'
    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': stock_msg or msg,
            'cart_item_count': cart.total_items,
            'cart_subtotal': str(cart.subtotal),
        })
    messages.success(request, stock_msg or msg)
    return redirect(request.META.get('HTTP_REFERER', 'store:shop'))


@require_POST
def update_cart_item(request, item_id):
    cart = request.cart
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        item.delete()
        messages.success(request, 'Item removed from your cart.')
    else:
        available_stock = item.available_stock
        if quantity > available_stock:
            quantity = available_stock
            messages.warning(request, f'Only {available_stock} in stock — quantity adjusted.')
        item.quantity = quantity
        item.save()

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'cart_item_count': cart.total_items,
            'subtotal': str(cart.subtotal),
            'shipping_cost': str(cart.shipping_cost),
            'total': str(cart.total),
            'line_total': str(item.line_total) if quantity > 0 else '0.00',
            'removed': quantity <= 0,
        })
    return redirect('cart:cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    cart = request.cart
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    product_name = item.product.name
    item.delete()

    if _is_ajax(request):
        return JsonResponse({'success': True, 'cart_item_count': cart.total_items, 'subtotal': str(cart.subtotal)})

    messages.success(request, f'Removed "{product_name}" from your cart.')
    return redirect('cart:cart_detail')
