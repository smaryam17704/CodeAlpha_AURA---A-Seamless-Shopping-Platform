import re

from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from store.models import Category, Product, NewsletterSubscriber
from .forms import ContactForm


def home(request):
    from reviews.models import Review

    featured_products = Product.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True).select_related('category')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    curated = Product.objects.filter(is_active=True).select_related('category').order_by('?')[:4]
    testimonials = Review.objects.filter(rating__gte=4).select_related('user', 'product').order_by('-created_at')[:6]

    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'curated': curated,
        'testimonials': testimonials,
    }
    return render(request, 'core/home.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks for reaching out — our team will get back to you shortly.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})


@require_POST
def newsletter_signup(request):
    email = request.POST.get('email', '').strip()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        validate_email(email)
    except ValidationError:
        msg, ok = 'Please enter a valid email address.', False
    else:
        _, created = NewsletterSubscriber.objects.get_or_create(email=email)
        msg = 'You are subscribed. Welcome to the AURA journal.' if created else 'You are already subscribed.'
        ok = True

    if is_ajax:
        from django.http import JsonResponse
        return JsonResponse({'success': ok, 'message': msg})

    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def journal(request):
    return render(request, 'core/journal.html')


def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def error_403(request, exception):
    return render(request, 'errors/403.html', status=403)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
