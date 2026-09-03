from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, NewsletterSubscriber


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('color', 'size', 'material', 'sku', 'price_override', 'stock_quantity', 'is_default', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'has_image', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(boolean=True, description='Image')
    def has_image(self, obj):
        return bool(obj.image_url)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'stock_quantity', 'availability_status', 'variant_count', 'is_featured', 'is_new_arrival', 'is_active')
    list_filter = ('category', 'is_active', 'is_featured', 'is_new_arrival')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline, ProductImageInline]
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('price', 'stock_quantity', 'is_featured', 'is_new_arrival', 'is_active')

    @admin.display(description='Variants')
    def variant_count(self, obj):
        return obj.variants.count()


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'label', 'sku', 'effective_price', 'stock_quantity', 'is_default', 'is_active')
    list_filter = ('is_active', 'is_default')
    search_fields = ('product__name', 'sku', 'color', 'size')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    search_fields = ('email',)
