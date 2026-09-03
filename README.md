# AURA — Find Your Kind of Extraordinary.

A full-stack e-commerce platform built with **Django, Python, HTML5, CSS3, Vanilla JavaScript, and SQLite** (via Django ORM). No frontend framework, no separate API layer — Django renders the templates, handles the business logic, and talks to the database directly.

---

## 1. Project Overview

AURA is a premium, editorial-style storefront selling considered lifestyle goods across **14 categories** (Apparel, Outerwear, Footwear, Bags & Wallets, Jewelry & Watches, Accessories, Beauty & Fragrance, Home & Living, Lighting & Candles, Tableware & Kitchen, Textiles & Bath, Stationery & Workspace, Tech Accessories, Travel) with **128 real products** and **401 database-backed variants** (size/color/material). It covers the full commerce lifecycle — browse → search/filter → product detail → variant selection → Add to Cart *or* Buy Now → checkout with coupons → order → order tracking with notifications → reviews — plus account preferences, wishlist, a contact form, and a Django-admin-powered back office.

---

## 2. Features

**Storefront**
- Editorial landing page (hero, category discovery with imagery, featured/new-arrival rails, brand story, customer reviews, philosophy section, newsletter)
- Server-side search, category/price/**rating**/availability filtering, and sorting — all combinable (`/shop/?q=...&category=...&min_rating=4&sort=...`)
- Product detail pages with gallery, **real database-backed variant selection** (size/color/material — price, stock, and SKU update live), stock-aware Add to Cart, **Buy Now**, related products, and session-based "recently viewed"
- **Quick View** modal — inspect a product (image, price, rating, variants, add to cart) without leaving the listing, powered by a live JSON endpoint
- Product reviews, gated to verified purchasers, with average rating display
- Light/dark theme toggle, persisted in `localStorage`, with an authenticated user's saved preference used as a fallback default
- Fully responsive (desktop → narrow mobile) with a working mobile navigation drawer and filter drawer

**Commerce**
- Guest carts (session-based) that automatically merge into the user's cart on login, correctly matching on product **and variant**
- AJAX add/update/remove-from-cart with live subtotal/shipping/total updates and server-side stock clamping (variant-aware)
- **Buy Now** — a session-based single-item checkout path that reuses the same atomic order-creation logic as the cart, without touching the user's actual cart
- **Coupons** — real database-backed codes (percentage or fixed discount, minimum order amount, expiry) validated and applied server-side at checkout (`AURA10`, `WELCOME15`, `FLAT500` seeded as demo codes)
- Checkout that server-side recalculates prices, validates stock with row-locking inside `transaction.atomic()`, applies any coupon, creates the `Order` + `OrderItem` records (snapshotting the selected variant), decrements stock, and clears the cart/Buy-Now session — all in one atomic operation
- Orders track **payment status** (pending/paid/failed/refunded — set realistically based on payment method) and a **discount** field alongside subtotal/shipping/total
- Order status flow: Pending → Confirmed → Processing → Shipped → **Out for Delivery** → Delivered (or Cancelled), shown as a visual stepper
- Order history, order detail, and strict per-user order ownership (`404`, not another user's data, if you try to view someone else's order)
- Wishlist (authenticated, database-backed, AJAX toggle)
- Address book (create/edit/delete/default), reused at checkout

**Accounts & Notifications**
- Django's built-in authentication (registration, login, logout, password validation, CSRF protection)
- Account dashboard summarizing recent orders, wishlist, and addresses
- **Account Preferences** — theme preference, newsletter opt-in, and order-update email opt-in, persisted per user
- **Notifications** — a real database-backed notification is created when an order is placed and whenever its status changes (via admin or checkout), visible in a dedicated notifications page with unread-count badges in the nav and mobile drawer

**Contact & Admin**
- **Contact page** — a real Django form (name/email/subject/message) with server-side validation, persisted to the database and visible in Django admin
- Full Django admin for products (with inline variant + gallery-image management), categories (with editorial imagery), orders (inline order items, status + payment-status editing that auto-notifies the customer), reviews, addresses, carts, coupons, contact messages, and notifications

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django 6.1 |
| ORM / Database | Django ORM + SQLite |
| Frontend | Django Templates, HTML5, CSS3 (hand-written, custom design system), Vanilla JavaScript |
| Auth | Django's built-in `django.contrib.auth` |
| Admin | Django's built-in admin site |
| Deployment target | Replit |

No React, Vue, Node.js, Express, Tailwind, Bootstrap, or DRF are used anywhere in this codebase.

---

## 4. Architecture

```
Browser → Django URLs → Django Views → Forms/Validation → Django ORM → SQLite
Frontend: Django Templates + HTML5 + CSS3 + Vanilla JS
```

Apps (each with its own models/views/urls/admin):

- **core** — landing page, journal, newsletter, **contact form**, global context processors, error handlers
- **accounts** — registration/login/logout, account dashboard, addresses, **preferences**
- **store** — categories (with imagery), products, **product variants**, catalog/search/filter/sort/**rating filter**, product detail, **quick view**, recently viewed
- **cart** — guest+authenticated cart via middleware (`cart/middleware.py`), variant-aware AJAX endpoints
- **wishlist** — authenticated wishlist, AJAX toggle
- **orders** — checkout, **Buy Now**, **coupons**, atomic order creation, order history/detail
- **reviews** — purchase-gated product reviews
- **notifications** — database-backed order/account notifications (new app)

---

## 5. Database Structure

```
Category (image_url) 1→N Product 1→N ProductVariant (size/color/material/SKU/stock/price_override)
Category 1→N Product 1→N ProductImage
User 1→1 Cart 1→N CartItem →N:1→ Product, →N:1→ ProductVariant
User 1→N Order 1→N OrderItem (snapshots product_name, sku, variant_label, unit_price at purchase time)
Order →N:1→ Coupon (discount_type, discount_value, minimum_order_amount, expiry_date)
User 1→N WishlistItem, Address, Review, Notification
Profile (1:1 User) — theme_preference, newsletter_opt_in, order_update_emails
ContactMessage — name, email, subject, message
```

Full model definitions live in each app's `models.py`.

---

## 6. Installation & Setup (local)

```bash
# 1. Clone / unzip the project, then:
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Seed the product catalog (128 products, 401 variants, across 14 categories,
#    plus demo reviews and demo coupons)
python manage.py seed_data

# 4. Create an admin user
python manage.py createsuperuser

# 5. Run the dev server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the storefront and `http://127.0.0.1:8000/admin/` for the admin panel.

---

## 7. Running on Replit

1. Import this project into Replit (or upload the zip).
2. Replit will use the included `.replit` / `replit.nix` config. On first run it will:
   - `pip install -r requirements.txt` (Replit does this automatically when it detects the file)
   - Run migrations, collect static files, and start the server on port 8080
3. Run `python manage.py seed_data` once from the Replit shell to populate the catalog.
4. Run `python manage.py createsuperuser` from the Replit shell to create an admin login.
5. Set a real `SECRET_KEY` environment variable in Replit's Secrets panel for anything beyond a demo (a default dev key is used otherwise).

---

## 8. Seed Data

```bash
python manage.py seed_data
```

Creates 14 categories (each with editorial imagery), **128 realistic products** (name, description, price in ₹, stock, material, SKU) with **401 product variants** where relevant (apparel sizes/colors, shoe sizes, ring sizes, fragrance volumes, etc.), **24 demo reviews** from 6 demo reviewer accounts, and **3 demo coupons** (`AURA10`, `WELCOME15`, `FLAT500`). Safe to run again: on an empty database it bootstraps the initial catalog; once products already exist, it preserves existing categories, products, variants, and coupon settings and does not overwrite or recreate administrator-managed records.

---

## 9. Admin Setup

```bash
python manage.py createsuperuser
```

Then log in at `/admin/`. From there you can manage products and their variants (inline), categories and their imagery, orders (including status and payment-status — editing an order's status automatically sends the customer a notification), reviews, addresses, carts, coupons, contact messages, and notifications.

---

## 10. Testing

An automated Django test suite (**105 tests**) covers:

- Registration/login/logout, catalog search/filter/sort/**rating filter**, cart (guest→auth merge, stock clamping, out-of-stock rejection — **variant-aware**)
- The full checkout → order → stock-reduction flow, order ownership protection
- **Product variants** — creation, default-variant resolution, label/price-override logic, cart integration, out-of-stock rejection
- **Buy Now** — login requirement, redirect to checkout, correct order creation without touching the real cart, variant support
- **Coupons** — valid application with correct discount math, invalid-code rejection, minimum-order enforcement
- **Payment status & Out for Delivery** — COD marked pending, card/UPI marked paid, `out_for_delivery` present in the status flow and displayed correctly
- **Contact form** — valid/invalid submission, database persistence, visibility in admin
- **Account preferences** — persistence, profile auto-creation on registration
- **Notifications** — creation on order placement and status change, unread-count badges, mark-as-read on view
- Purchase-gated reviews (including duplicate-review blocking), newsletter signup validation, the custom 404 error page (verified under `DEBUG=False`), and admin authorization + full CRUD

```bash
python manage.py test
```

All 105 tests pass as of this build. `python manage.py check` and `python manage.py makemigrations --check` both pass cleanly with no issues or pending migrations.

Beyond the automated suite, the following were manually exercised end-to-end against a running server during this enhancement pass and confirmed working: registration (with automatic `Profile` creation), Buy Now with a selected variant → checkout → order confirmation (verified in the database: correct discount math, correct variant stock decrement, correct payment status, real cart left untouched), coupon-code checkout, Quick View's live JSON endpoint, notification creation and read-state, theme-preference persistence reflected in the rendered page, and admin visibility for every new model (coupons, contact messages, variants, notifications). One real bug was caught and fixed during this process: the Quick View JavaScript was fetching an incorrect URL path — found via a full page-by-page smoke test and corrected before delivery.

---

## 10a. Catalog Quality-Control Pass (this build)

This build went through an explicit catalog audit on top of the existing 121-product base:

- **Removed 5 products** that were artificial "padding" — near-identical concepts distinguished only by a generic adjective (e.g. "Vintage/Classic/Everyday Brown Leather Boot", "Compact/Structured Leather Wallet") with no genuinely distinct silhouette, material, or use case.
- **Added 12 new products**, each individually sourced: the image for every new product was pulled from a live, human-captioned photo whose own caption/alt-text was checked against the product name before use (e.g. "Belted Wool Trench Coat" is backed by a photo captioned "a man in a trench coat walking down the street").
- **Final catalog: 128 products, 401 variants, 0 duplicate SKUs, 0 duplicate image URLs, 0 blank image URLs** — verified by direct database query after a real `seed_data` run, not by code inspection alone.
- Regression tests were added (`store/tests_catalog_integrity.py`) to lock in: no blank/duplicate images, no duplicate SKUs, every product has a category, seeding is idempotent, and the specific removed near-duplicates don't silently reappear.
- **This did not reach the ~183–185 product / ~100-new-product target requested.** See Known Limitations below for why, and what a genuine path to that number looks like.

---

## 11. Known Limitations

Being transparent about what has **not** been independently verified, so nothing here is overstated:

- **No real payment gateway.** Card/UPI options at checkout are recorded as selected payment methods (and marked `paid` for realism) but no external processor is contacted — this matches the original brief ("payment integration is not required").
- **No headless browser was available in this build environment** to capture visual screenshots or verify pixel-level responsive/zoom behavior (80–200%) — the CSS was written with `clamp()`, fluid grids, and explicit breakpoints, and every new component (variant selector, Quick View modal, rating filter, notification bell, category imagery) reuses the existing responsive design system, but a human visual pass on a real browser is recommended before treating this as pixel-perfect.
- **Product photography** uses curated Unsplash imagery matched to each product's category and description (via `image_url`), not custom photography — swap in real product photos via the `image` field in the admin when available. A graceful `onerror` fallback to a branded placeholder SVG is wired into every product image on every page, so a stale image URL degrades gracefully rather than breaking layout.
- **Email is console-only** (`EMAIL_BACKEND = console`) — no real email is sent for registration/order confirmation/notifications; wire up a real SMTP backend for production use. In-app notifications (the `/notifications/` page) work fully regardless.
- **Admin analytics dashboard** — not built as a separate custom view; Django admin's built-in list views, filters, and search (e.g. filtering orders by status/payment-status, products by stock/category) cover the "useful admin visibility" requirement without adding a bespoke dashboard, per the brief's explicit instruction not to over-engineer this.
- **Quick View's variant handling** is intentionally simpler than the full product-detail page (a single dropdown, no live stock-badge swap) to keep it fast and low-risk within the time available — "View Full Product" always links through to the complete experience.
- `ALLOWED_HOSTS = ['*']` and a default `SECRET_KEY` are used for easy Replit demo access — set a real `SECRET_KEY` env var and restrict `ALLOWED_HOSTS` before treating this as production-grade.
- **Catalog size fell short of the ~183–185 product target (12 new vs. ~100 requested).** Sourcing a genuinely relevant, individually-verified image for each new product requires finding a live photo whose own caption confirms the subject, then hand-checking it — there's no way in this environment to bulk-fetch and verify dozens of arbitrary external image URLs at once, so each new product realistically costs a search-and-verify cycle. Getting to ~100 new products at the same verification standard is achievable but needs a much longer, likely multi-session pass rather than a single sitting. The 116 retained legacy products (121 minus the 5 removed) were audited *structurally* (name/category consistency, dedup, field completeness) but not re-verified image-by-image, since this environment has no way to fetch arbitrary pre-existing external URLs for inspection — only images that surface through a live search can be visually confirmed. Flagged near-duplicate concepts among the legacy set (the boots/wallets) were removed; anything not flagged was left as-is rather than guessed at.

---

## 12. Project Structure

```
aura/
├── manage.py
├── requirements.txt
├── .replit / replit.nix
├── aura_project/          settings, root urls, wsgi/asgi
├── core/                  home, journal, newsletter, contact form, context processors, error handlers
├── accounts/              auth, addresses, account dashboard, preferences
├── store/                 categories, products, product variants, catalog, quick view, seed_data command, tests
├── cart/                  cart models (variant-aware), AJAX views, guest/auth middleware
├── wishlist/              wishlist models + AJAX views
├── orders/                checkout, buy now, coupons, atomic order creation, order history/detail
├── reviews/                purchase-gated reviews
├── notifications/          order/account notifications
├── templates/              base.html + all page/include templates
├── static/                 css/ (themes, base, components, responsive), js/ (9 modules incl. quick-view.js), images/ (logo, fallback)
└── media/                  uploaded product images (if any are added via admin)
```
