def wishlist_context(request):
    if request.user.is_authenticated:
        ids = list(request.user.wishlist_items.values_list('product_id', flat=True))
        return {'wishlist_product_ids': ids, 'wishlist_count': len(ids)}
    return {'wishlist_product_ids': [], 'wishlist_count': 0}
