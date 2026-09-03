from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from store.models import Product
from .models import WishlistItem


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


@login_required
def wishlist_detail(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('product', 'product__category')
    return render(request, 'wishlist/wishlist.html', {'items': items})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if created:
        added = True
        msg = f'Added "{product.name}" to your wishlist.'
    else:
        item.delete()
        added = False
        msg = f'Removed "{product.name}" from your wishlist.'

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'added': added,
            'message': msg,
            'wishlist_count': WishlistItem.objects.filter(user=request.user).count(),
        })
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'store:shop'))


@login_required
@require_POST
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    item.delete()
    messages.success(request, 'Removed from your wishlist.')
    return redirect('wishlist:wishlist_detail')
