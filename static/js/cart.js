// AURA — Cart interactions: AJAX add-to-cart, quantity steppers, cart page updates.
document.addEventListener('DOMContentLoaded', () => {

  function updateCartBadge(count) {
    document.querySelectorAll('[data-cart-count]').forEach((el) => {
      el.textContent = count;
      el.style.display = count > 0 ? 'flex' : 'none';
    });
  }

  // Quantity steppers (product detail + cart page) — purely UI, real value submitted with form/AJAX
  document.querySelectorAll('.qty-stepper').forEach((stepper) => {
    const input = stepper.querySelector('input');
    const max = parseInt(input.getAttribute('max') || '999', 10);
    stepper.querySelectorAll('[data-step]').forEach((btn) => {
      btn.addEventListener('click', () => {
        let val = parseInt(input.value || '1', 10);
        const delta = parseInt(btn.dataset.step, 10);
        val = Math.min(Math.max(1, val + delta), max);
        input.value = val;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });
  });

  // Add to cart forms (product cards + product detail) via AJAX
  document.querySelectorAll('form[data-add-to-cart]').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const originalHTML = btn ? btn.innerHTML : '';
      if (btn) {
        btn.classList.add('is-loading');
        btn.disabled = true;
      }
      const formData = new FormData(form);
      const params = {};
      formData.forEach((v, k) => { params[k] = v; });

      try {
        const { ok, data } = await window.AURA.postForm(form.action, params);
        if (data) {
          window.AURA.toast(data.message, data.success ? 'success' : 'error');
          if (data.success && typeof data.cart_item_count !== 'undefined') {
            updateCartBadge(data.cart_item_count);
          }
        } else if (!ok) {
          window.AURA.toast('Something went wrong. Please try again.', 'error');
        }
      } catch (err) {
        window.AURA.toast('Network error — please try again.', 'error');
      } finally {
        if (btn) {
          btn.classList.remove('is-loading');
          btn.disabled = false;
          btn.innerHTML = originalHTML;
        }
      }
    });
  });

  // Cart page: live quantity update
  document.querySelectorAll('[data-cart-item-form]').forEach((form) => {
    const input = form.querySelector('input[name="quantity"]');
    let debounceTimer;

    const submitUpdate = async () => {
      const params = { quantity: input.value };
      const { data } = await window.AURA.postForm(form.action, params);
      if (data && data.success) {
        const row = form.closest('[data-cart-row]');
        if (data.removed && row) {
          row.style.transition = 'opacity 0.25s ease';
          row.style.opacity = '0';
          setTimeout(() => {
            row.remove();
            if (data.cart_item_count === 0) window.location.reload();
          }, 250);
        } else if (row) {
          const lineTotalEl = row.querySelector('[data-line-total]');
          if (lineTotalEl) lineTotalEl.textContent = '₹' + Number(data.line_total).toLocaleString('en-IN', { minimumFractionDigits: 2 });
        }
        updateCartBadge(data.cart_item_count);
        const subtotalEl = document.querySelector('[data-cart-subtotal]');
        const shippingEl = document.querySelector('[data-cart-shipping]');
        const totalEl = document.querySelector('[data-cart-total]');
        if (subtotalEl) subtotalEl.textContent = '₹' + Number(data.subtotal).toLocaleString('en-IN', { minimumFractionDigits: 2 });
        if (shippingEl) shippingEl.textContent = Number(data.shipping_cost) === 0 ? 'Free' : '₹' + Number(data.shipping_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 });
        if (totalEl) totalEl.textContent = '₹' + Number(data.total).toLocaleString('en-IN', { minimumFractionDigits: 2 });
      }
    };

    if (input) {
      input.addEventListener('change', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(submitUpdate, 350);
      });
    }
  });

  // Remove item buttons on cart page (AJAX with fade-out)
  document.querySelectorAll('[data-remove-item]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const row = btn.closest('[data-cart-row]');
      const { data } = await window.AURA.postForm(btn.dataset.removeItem, {});
      if (data && data.success) {
        window.AURA.toast('Item removed from your cart.', 'success');
        updateCartBadge(data.cart_item_count);
        if (row) {
          row.style.transition = 'opacity 0.25s ease';
          row.style.opacity = '0';
          setTimeout(() => {
            row.remove();
            if (data.cart_item_count === 0) window.location.reload();
          }, 250);
        }
      }
    });
  });
});
