from django import forms
from accounts.models import Address


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    address_line1 = forms.CharField(max_length=200, label='Address line 1')
    address_line2 = forms.CharField(max_length=200, required=False, label='Address line 2 (optional)')
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)
    country = forms.CharField(max_length=100, initial='India')
    payment_method = forms.ChoiceField(
        choices=[
            ('cash_on_delivery', 'Cash on Delivery'),
            ('card', 'Credit / Debit Card (simulated)'),
            ('upi', 'UPI (simulated)'),
        ],
        widget=forms.RadioSelect,
        initial='cash_on_delivery',
    )
    save_address = forms.BooleanField(required=False, initial=False, label='Save this address to my account')
    coupon_code = forms.CharField(max_length=30, required=False, label='Coupon Code')
