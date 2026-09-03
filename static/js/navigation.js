// AURA — Navigation behavior: scroll elevation, mobile drawer, search overlay.
document.addEventListener('DOMContentLoaded', () => {
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('is-scrolled', window.scrollY > 12);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Mobile drawer
  const drawer = document.querySelector('.mobile-drawer');
  const backdrop = document.querySelector('.mobile-drawer-backdrop');
  const openBtn = document.querySelector('[data-drawer-open]');
  const closeBtn = document.querySelector('[data-drawer-close]');

  function openDrawer() {
    if (!drawer || !backdrop) return;
    drawer.classList.add('is-open');
    backdrop.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    const firstLink = drawer.querySelector('a, button');
    if (firstLink) firstLink.focus();
  }
  function closeDrawer() {
    if (!drawer || !backdrop) return;
    drawer.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (openBtn) openBtn.focus();
  }
  if (openBtn) openBtn.addEventListener('click', openDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDrawer();
  });

  // Search overlay
  const searchOverlay = document.querySelector('.search-overlay');
  const searchOpenBtns = document.querySelectorAll('[data-search-open]');
  const searchCloseBtn = document.querySelector('[data-search-close]');

  function openSearch() {
    if (!searchOverlay) return;
    searchOverlay.classList.add('is-open');
    const input = searchOverlay.querySelector('input[type="search"], input[name="q"]');
    if (input) setTimeout(() => input.focus(), 80);
    document.body.style.overflow = 'hidden';
  }
  function closeSearch() {
    if (!searchOverlay) return;
    searchOverlay.classList.remove('is-open');
    document.body.style.overflow = '';
  }
  searchOpenBtns.forEach((btn) => btn.addEventListener('click', openSearch));
  if (searchCloseBtn) searchCloseBtn.addEventListener('click', closeSearch);
  if (searchOverlay) {
    searchOverlay.addEventListener('click', (e) => {
      if (e.target === searchOverlay) closeSearch();
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && searchOverlay && searchOverlay.classList.contains('is-open')) closeSearch();
  });
});
