from .models import Cart


class CartMiddleware:
    """
    Ensures request.cart always resolves to the correct Cart:
    - authenticated user -> DB cart tied to user (created lazily)
    - guest -> DB cart tied to session key (created lazily)
    Also merges a guest cart into the user cart the moment a guest logs in.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.session_key:
            request.session.save()

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)

            # Merge any guest cart that existed under this session
            guest_session_key = request.session.get('guest_cart_key')
            if guest_session_key and guest_session_key != request.session.session_key:
                self._merge_carts(guest_session_key, cart)
                del request.session['guest_cart_key']

            session_key = request.session.session_key
            guest_cart = Cart.objects.filter(session_key=session_key).exclude(pk=cart.pk).first()
            if guest_cart:
                self._merge_cart_objects(guest_cart, cart)

            request.cart = cart
        else:
            session_key = request.session.session_key
            request.session['guest_cart_key'] = session_key
            cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
            request.cart = cart

        response = self.get_response(request)
        return response

    def _merge_carts(self, guest_session_key, user_cart):
        guest_cart = Cart.objects.filter(session_key=guest_session_key).first()
        if guest_cart:
            self._merge_cart_objects(guest_cart, user_cart)

    def _merge_cart_objects(self, guest_cart, user_cart):
        for item in guest_cart.items.all():
            existing = user_cart.items.filter(product=item.product, variant=item.variant).first()
            stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
            if existing:
                new_qty = existing.quantity + item.quantity
                existing.quantity = min(new_qty, stock or new_qty)
                existing.save()
            else:
                item.pk = None
                item.cart = user_cart
                item.quantity = min(item.quantity, stock or item.quantity)
                item.save()
        guest_cart.delete()
