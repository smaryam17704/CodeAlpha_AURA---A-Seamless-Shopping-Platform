// AURA — Wishlist toggle interactions.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-wishlist-toggle]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const url = btn.dataset.wishlistToggle;

      const { status, data } = await window.AURA.postForm(url, {});

      if (status === 403 || status === 401 || (data && data.redirect)) {
        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        return;
      }
      if (!data) return;

      if (data.success) {
        btn.classList.toggle('is-active', data.added);
        btn.setAttribute('aria-pressed', data.added ? 'true' : 'false');
        window.AURA.toast(data.message, 'success');
        document.querySelectorAll('[data-wishlist-count]').forEach((el) => {
          el.textContent = data.wishlist_count;
        });
        // If on wishlist page itself and removed, fade the card out
        if (!data.added) {
          const row = btn.closest('[data-wishlist-row]');
          if (row) {
            row.style.transition = 'opacity 0.25s ease';
            row.style.opacity = '0';
            setTimeout(() => row.remove(), 250);
          }
        }
      }
    });
  });
});
