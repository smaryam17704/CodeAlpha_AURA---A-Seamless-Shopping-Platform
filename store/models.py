from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, help_text='External editorial image representing this category.')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:category_detail', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')

    short_description = models.CharField(max_length=250, blank=True)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Original price to display as struck-through, if this item is discounted.'
    )

    sku = models.CharField(max_length=40, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text='Fallback external image URL if no file uploaded.')

    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    material = models.CharField(max_length=120, blank=True)
    weight = models.CharField(max_length=60, blank=True, help_text='Display weight, e.g. "180g"')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['is_active', 'is_new_arrival']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f'{base_slug}-{counter}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return ''

    @property
    def is_on_sale(self):
        return bool(self.compare_at_price and self.compare_at_price > self.price)

    @property
    def discount_percent(self):
        if self.is_on_sale:
            return round((1 - (self.price / self.compare_at_price)) * 100)
        return 0

    @property
    def availability_status(self):
        if self.stock_quantity == 0:
            return 'out_of_stock'
        if self.stock_quantity <= 5:
            return 'low_stock'
        return 'available'

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(avg=models.Avg('rating'))
        return round(agg['avg'] or 0, 1)

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def has_variants(self):
        return self.variants.filter(is_active=True).exists()

    @property
    def default_variant(self):
        return self.variants.filter(is_active=True).order_by('-is_default', 'id').first()


class ProductVariant(models.Model):
    """
    A real, database-backed purchasable variation of a product (size/color/material).
    Not every product needs variants — products with none simply sell as-is.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=30, blank=True)
    color = models.CharField(max_length=40, blank=True)
    material = models.CharField(max_length=80, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Leave blank to use the base product price for this variant.'
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} — {self.label}'

    def save(self, *args, **kwargs):
        if self.is_default:
            ProductVariant.objects.filter(product=self.product, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def label(self):
        parts = [p for p in [self.color, self.size, self.material] if p]
        return ' / '.join(parts) if parts else self.sku

    @property
    def effective_price(self):
        return self.price_override if self.price_override is not None else self.product.price

    @property
    def in_stock(self):
        return self.stock_quantity > 0


class ProductImage(models.Model):
    """Additional gallery images for a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/', blank=True, null=True)
    image_url = models.URLField(blank=True)
    alt_text = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f'{self.product.name} - image {self.display_order}'

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email
