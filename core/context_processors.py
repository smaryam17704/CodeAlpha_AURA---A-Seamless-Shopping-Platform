def site_context(request):
    """Global site-wide context: brand info + nav categories available in every template."""
    from store.models import Category
    return {
        'SITE_NAME': 'AURA',
        'SITE_TAGLINE': 'Find Your Kind of Extraordinary.',
        'footer_categories': Category.objects.filter(is_active=True)[:5],
    }
