// AURA — Shop filter interactions: mobile filter drawer, auto-submit selects.
document.addEventListener('DOMContentLoaded', () => {
  const filterPanel = document.querySelector('.shop-filters');
  const openBtn = document.querySelector('[data-filters-open]');
  const closeBtn = document.querySelector('[data-filters-close]');
  const backdrop = document.querySelector('[data-filters-backdrop]');

  function openFilters() {
    if (!filterPanel) return;
    filterPanel.classList.add('is-open');
    if (backdrop) backdrop.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
  function closeFilters() {
    if (!filterPanel) return;
    filterPanel.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-open');
    document.body.style.overflow = '';
  }
  if (openBtn) openBtn.addEventListener('click', openFilters);
  if (closeBtn) closeBtn.addEventListener('click', closeFilters);
  if (backdrop) backdrop.addEventListener('click', closeFilters);

  // Auto-submit the sort dropdown
  const sortSelect = document.querySelector('[data-sort-select]');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      sortSelect.form.submit();
    });
  }
});
