// AURA — Toast system + shared helpers.
window.AURA = (function () {
  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match.pop()) : '';
  }

  const csrfToken = getCookie('csrftoken');

  function ensureStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      stack.setAttribute('role', 'status');
      stack.setAttribute('aria-live', 'polite');
      document.body.appendChild(stack);
    }
    return stack;
  }

  function toast(message, type) {
    type = type || 'info';
    const stack = ensureStack();
    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.innerHTML =
      '<span class="toast-msg"></span>' +
      '<button class="toast-close" aria-label="Dismiss notification">&times;</button>';
    el.querySelector('.toast-msg').textContent = message;
    stack.appendChild(el);

    const remove = () => {
      el.classList.add('is-leaving');
      setTimeout(() => el.remove(), 260);
    };
    el.querySelector('.toast-close').addEventListener('click', remove);
    const timer = setTimeout(remove, 4200);
    el.addEventListener('mouseenter', () => clearTimeout(timer));
  }

  async function postForm(url, data) {
    const body = new URLSearchParams(data || {});
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    });
    let json = null;
    try { json = await res.json(); } catch (e) { /* non-JSON response */ }
    return { ok: res.ok, status: res.status, data: json };
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Promote server-rendered Django messages into toasts
    document.querySelectorAll('[data-flash-message]').forEach((el) => {
      toast(el.dataset.flashMessage, el.dataset.flashType || 'info');
      el.remove();
    });

    // Newsletter forms (footer + landing page section) submit via AJAX
    document.querySelectorAll('[data-newsletter-form]').forEach((form) => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = form.querySelector('input[name="email"]');
        const { data } = await postForm(form.action, { email: input.value });
        if (data) {
          toast(data.message, data.success ? 'success' : 'error');
          if (data.success) input.value = '';
        }
      });
    });
  });

  return { toast, postForm, csrfToken };
})();
