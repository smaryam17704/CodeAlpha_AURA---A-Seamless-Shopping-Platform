from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET

from .models import Category, Product
from reviews.models import Review
from reviews.forms import ReviewForm

RECENTLY_VIEWED_SESSION_KEY = 'recently_viewed_ids'
RECENTLY_VIEWED_MAX = 8


def _apply_filters_and_sort(request, base_qs):
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    availability = request.GET.get('availability', '').strip()
    collection = request.GET.get('collection', '').strip()  # featured / new
    min_rating = request.GET.get('min_rating', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    qs = base_qs.annotate(avg_rating=Avg('reviews__rating'))

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(short_description__icontains=q) |
            Q(sku__icontains=q) |
            Q(category__name__icontains=q)
        )

    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    if min_price:
        try:
            qs = qs.filter(price__gte=Decimal(min_price))
        except InvalidOperation:
            pass

    if max_price:
        try:
            qs = qs.filter(price__lte=Decimal(max_price))
        except InvalidOperation:
            pass

    if availability == 'in_stock':
        qs = qs.filter(stock_quantity__gt=0)
    elif availability == 'out_of_stock':
        qs = qs.filter(stock_quantity=0)

    if collection == 'featured':
        qs = qs.filter(is_featured=True)
    elif collection == 'new':
        qs = qs.filter(is_new_arrival=True)

    if min_rating:
        try:
            qs = qs.filter(avg_rating__gte=Decimal(min_rating))
        except InvalidOperation:
            pass

    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'featured': '-is_featured',
        'name_az': 'name',
    }
    qs = qs.order_by(sort_map.get(sort, '-created_at'))

    return qs, {
        'q': q, 'category': category_slug, 'min_price': min_price, 'max_price': max_price,
        'availability': availability, 'collection': collection, 'min_rating': min_rating, 'sort': sort,
    }


@require_GET
def shop(request):
    base_qs = Product.objects.filter(is_active=True).select_related('category')
    qs, active_filters = _apply_filters_and_sort(request, base_qs)

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(is_active=True)

    # Preserve querystring (minus page) for pagination links
    querydict = request.GET.copy()
    querydict.pop('page', None)
    querystring = querydict.urlencode()

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'active_filters': active_filters,
        'querystring': querystring,
        'result_count': paginator.count,
    }
    return render(request, 'store/shop.html', context)


@require_GET
def search(request):
    return shop(request)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    base_qs = Product.objects.filter(is_active=True, category=category).select_related('category')
    qs, active_filters = _apply_filters_and_sort(request, base_qs)

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    querydict = request.GET.copy()
    querydict.pop('page', None)

    context = {
        'category': category,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': Category.objects.filter(is_active=True),
        'active_filters': active_filters,
        'querystring': querydict.urlencode(),
        'result_count': paginator.count,
    }
    return render(request, 'store/category_detail.html', context)


@require_GET
def quick_view(request, product_id):
    product = get_object_or_404(Product.objects.select_related('category'), pk=product_id, is_active=True)
    variants = [
        {
            'id': v.id, 'label': v.label, 'price': str(v.effective_price),
            'in_stock': v.in_stock, 'stock': v.stock_quantity,
        }
        for v in product.variants.filter(is_active=True)
    ]
    data = {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'category': product.category.name if product.category else '',
        'price': str(product.price),
        'compare_at_price': str(product.compare_at_price) if product.compare_at_price else None,
        'short_description': product.short_description,
        'image': product.display_image,
        'average_rating': product.average_rating,
        'review_count': product.review_count,
        'in_stock': product.in_stock,
        'stock_quantity': product.stock_quantity,
        'has_variants': product.has_variants,
        'variants': variants,
        'url': product.get_absolute_url(),
    }
    return JsonResponse(data)


def _track_recently_viewed(request, product_id):
    viewed = request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
    viewed = [pid for pid in viewed if pid != product_id]
    viewed.insert(0, product_id)
    viewed = viewed[:RECENTLY_VIEWED_MAX]
    request.session[RECENTLY_VIEWED_SESSION_KEY] = viewed


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('gallery_images', 'reviews__user'),
        slug=slug, is_active=True
    )

    _track_recently_viewed(request, product.id)

    related_products = Product.objects.filter(
        is_active=True, category=product.category
    ).exclude(pk=product.pk)[:4]

    recently_viewed_ids = [pid for pid in request.session.get(RECENTLY_VIEWED_SESSION_KEY, []) if pid != product.id]
    recently_viewed = Product.objects.filter(id__in=recently_viewed_ids, is_active=True)
    recently_viewed = sorted(recently_viewed, key=lambda p: recently_viewed_ids.index(p.id))[:4]

    reviews = product.reviews.select_related('user').order_by('-created_at')
    variants = product.variants.filter(is_active=True)
    default_variant = variants.filter(is_default=True).first() or variants.first()

    user_has_reviewed = False
    user_can_review = False
    review_form = None
    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(user=request.user).exists()
        has_purchased = product.order_items.filter(order__user=request.user, order__status__in=['delivered', 'shipped', 'processing', 'confirmed']).exists()
        user_can_review = has_purchased and not user_has_reviewed
        if user_can_review:
            review_form = ReviewForm()

    context = {
        'product': product,
        'related_products': related_products,
        'recently_viewed': recently_viewed,
        'reviews': reviews,
        'user_has_reviewed': user_has_reviewed,
        'user_can_review': user_can_review,
        'review_form': review_form,
        'variants': variants,
        'default_variant': default_variant,
    }
    return render(request, 'store/product_detail.html', context)
