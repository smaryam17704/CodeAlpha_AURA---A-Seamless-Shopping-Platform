def cart_context(request):
    cart = getattr(request, 'cart', None)
    if cart is None:
        return {'cart_item_count': 0}
    return {'cart_item_count': cart.total_items}
