// AURA — Quick View: fetches live product data and renders it into a shared modal.
document.addEventListener('DOMContentLoaded', () => {
  let modal = document.getElementById('quick-view-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'quick-view-modal';
    modal.className = 'modal-backdrop';
    modal.innerHTML = '<div class="modal quick-view-modal-inner"><div class="modal-head"><span>Quick View</span><button type="button" class="btn-icon" data-modal-close aria-label="Close">&times;</button></div><div class="modal-body" id="quick-view-content"></div></div>';
    document.body.appendChild(modal);

    modal.querySelector('[data-modal-close]').addEventListener('click', () => {
      modal.classList.remove('is-open');
      document.body.style.overflow = '';
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
      }
    });
  }

  function starString(rating) {
    const full = Math.round(rating || 0);
    let out = '';
    for (let i = 1; i <= 5; i++) {
      out += i <= full ? '★' : '<span class="empty">★</span>';
    }
    return out;
  }

  function formatINR(value) {
    return '₹' + Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function render(data) {
    const content = document.getElementById('quick-view-content');
    const variantOptions = (data.variants || []).map((v) =>
      `<option value="${v.id}" data-price="${v.price}" ${!v.in_stock ? 'disabled' : ''}>${v.label}${!v.in_stock ? ' — Out of Stock' : ''}</option>`
    ).join('');

    content.innerHTML = `
      <div class="quick-view-grid">
        <div class="quick-view-image">
          <img src="${data.image || '/static/images/product-fallback.svg'}" alt="${data.name}" onerror="this.onerror=null;this.src='/static/images/product-fallback.svg';">
        </div>
        <div class="quick-view-body">
          ${data.category ? `<span class="eyebrow">${data.category}</span>` : ''}
          <h3>${data.name}</h3>
          ${data.review_count > 0 ? `<div class="rating-row" style="margin-bottom:0.6rem;"><span class="stars">${starString(data.average_rating)}</span><span>${data.average_rating} · ${data.review_count} review${data.review_count === 1 ? '' : 's'}</span></div>` : ''}
          <div class="price-row" style="margin-bottom:0.75rem;">
            <span class="price" id="qv-price">${formatINR(data.price)}</span>
            ${data.compare_at_price ? `<span class="compare-price">${formatINR(data.compare_at_price)}</span>` : ''}
          </div>
          <p>${data.short_description || ''}</p>
          ${data.has_variants ? `<div class="field"><label>Options</label><select id="qv-variant-select" style="max-width:260px;">${variantOptions}</select></div>` : ''}
          <div style="display:flex; gap:0.75rem; margin-top:1rem; flex-wrap:wrap;">
            <button type="button" class="btn btn-primary" id="qv-add-to-cart" ${!data.in_stock ? 'disabled' : ''}>${data.in_stock ? 'Add to Cart' : 'Out of Stock'}</button>
            <a href="${data.url}" class="btn btn-outline">View Full Product</a>
          </div>
        </div>
      </div>
    `;

    const variantSelect = document.getElementById('qv-variant-select');
    if (variantSelect) {
      variantSelect.addEventListener('change', () => {
        const opt = variantSelect.options[variantSelect.selectedIndex];
        document.getElementById('qv-price').textContent = formatINR(opt.dataset.price);
        document.getElementById('qv-add-to-cart').disabled = opt.disabled;
      });
    }

    document.getElementById('qv-add-to-cart').addEventListener('click', async () => {
      const params = { quantity: 1 };
      if (variantSelect) params.variant_id = variantSelect.value;
      const { data: res } = await window.AURA.postForm(`/cart/add/${data.id}/`, params);
      if (res) {
        window.AURA.toast(res.message, res.success ? 'success' : 'error');
        if (res.success) {
          document.querySelectorAll('[data-cart-count]').forEach((el) => {
            el.textContent = res.cart_item_count;
            el.style.display = res.cart_item_count > 0 ? 'flex' : 'none';
          });
        }
      }
    });
  }

  document.addEventListener('click', async (e) => {
    const trigger = e.target.closest('[data-quick-view]');
    if (!trigger) return;
    const productId = trigger.dataset.quickView;
    document.getElementById('quick-view-content').innerHTML = '<div class="skeleton" style="height:320px;"></div>';
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';

    try {
      const resp = await fetch(`/quick-view/${productId}/`);
      const data = await resp.json();
      render(data);
    } catch (err) {
      document.getElementById('quick-view-content').innerHTML = '<p>Could not load this product. Please try again.</p>';
    }
  });
});
