// Shared layout (header/footer) + cart helpers, used by every page.

const CART_KEY = 'croid_cart';

function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}

function addToCart(item) {
  const cart = getCart();
  const existing = cart.find(
    (i) => i.id === item.id && i.size === item.size && i.color === item.color
  );
  if (existing) {
    existing.qty += item.qty;
  } else {
    cart.push(item);
  }
  saveCart(cart);
}

function removeFromCart(index) {
  const cart = getCart();
  cart.splice(index, 1);
  saveCart(cart);
}

function updateCartBadge() {
  const badge = document.getElementById('cart-count');
  if (!badge) return;
  const count = getCart().reduce((sum, i) => sum + Number(i.qty || 0), 0);
  badge.textContent = count > 0 ? `Заявка (${count})` : 'Заявка (0)';
}

async function fetchConfig() {
  const res = await fetch('/api/config');
  return res.json();
}

function renderLayout(activePage) {
  const header = document.getElementById('site-header');
  const footer = document.getElementById('site-footer');
  if (!header || !footer) return;

  fetchConfig().then((cfg) => {
    const nameParts = cfg.BRAND_NAME.split('.');
    const brandHtml =
      nameParts.length > 1
        ? `${nameParts[0]}<span class="dot">.${nameParts.slice(1).join('.')}</span>`
        : cfg.BRAND_NAME;

    const links = [
      { href: '/index.html', label: 'Главная', key: 'home' },
      { href: '/catalog.html', label: 'Каталог', key: 'catalog' },
      { href: '/about.html', label: 'О компании', key: 'about' },
      { href: '/contacts.html', label: 'Контакты', key: 'contacts' },
    ];
    const navHtml = links
      .map(
        (l) =>
          `<a href="${l.href}" class="${l.key === activePage ? 'active' : ''}">${l.label}</a>`
      )
      .join('');

    header.innerHTML = `
      <div class="container">
        <a href="/index.html" class="logo">${brandHtml}</a>
        <nav class="main-nav">${navHtml}</nav>
        <div class="header-actions">
          <a href="tel:${cfg.PHONE.replace(/[^+\d]/g, '')}">${cfg.PHONE}</a>
          <a href="/cart.html" class="cart-link" id="cart-count">Заявка (0)</a>
        </div>
      </div>
    `;

    footer.innerHTML = `
      <div class="container">
        <div>© ${new Date().getFullYear()} ${cfg.BRAND_NAME}. ${cfg.TAGLINE}.</div>
        <div>${cfg.PHONE} · ${cfg.EMAIL} · ${cfg.ADDRESS}</div>
      </div>
    `;

    updateCartBadge();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset.page || '';
  renderLayout(page);
});
