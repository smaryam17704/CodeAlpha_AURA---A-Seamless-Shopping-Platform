from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

from store.models import Product
from .forms import ReviewForm
from .models import Review


@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.info(request, 'You have already reviewed this product.')
        return redirect(product.get_absolute_url())

    has_purchased = product.order_items.filter(
        order__user=request.user,
        order__status__in=['delivered', 'shipped', 'processing', 'confirmed']
    ).exists()
    if not has_purchased:
        messages.error(request, 'Only customers who purchased this product can leave a review.')
        return redirect(product.get_absolute_url())

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.is_verified_purchase = True
        review.save()
        messages.success(request, 'Thank you — your review has been posted.')
    else:
        messages.error(request, 'Please provide a valid rating and comment.')

    return redirect(product.get_absolute_url())
