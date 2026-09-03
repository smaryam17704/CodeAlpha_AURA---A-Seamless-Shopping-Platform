from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Order
from wishlist.models import WishlistItem
from .forms import RegisterForm, ProfileUpdateForm, AddressForm, PreferencesForm
from .models import Address, Profile


def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to AURA, {user.first_name}!')
            return redirect('core:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


class AuraLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().first_name or form.get_user().username}!')
        return super().form_valid(form)


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been signed out.')
        return redirect('core:home')
    return render(request, 'accounts/logout_confirm.html')


@login_required
def account_dashboard(request):
    recent_orders = Order.objects.filter(user=request.user)[:3]
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/dashboard.html', {
        'recent_orders': recent_orders,
        'wishlist_count': wishlist_count,
        'addresses': addresses,
    })


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:account_dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def preferences(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PreferencesForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been saved.')
            return redirect('accounts:preferences')
    else:
        form = PreferencesForm(instance=profile)
    return render(request, 'accounts/preferences.html', {'form': form})


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address saved.')
            return redirect('accounts:address_list')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'is_edit': False})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated.')
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form, 'is_edit': True, 'address': address})


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, 'Address removed.')
    return redirect('accounts:address_list')
