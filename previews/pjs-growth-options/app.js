const photoBase = 'https://pjscactuslodge.com';
const products = [
  { sku:'PJS-017', name:'Aztekium hinotonni', price:35, detail:'3 in tall · 3.5 in pot', photo:'/api/photo/d5b7d350-bb04-4ace-9091-974d7d92de29' },
  { sku:'PJS-023', name:'Stenocactus crispatus “Brain cactus”', price:25, detail:'2 in tall · one exact plant', photo:'/api/photo/d8b62fcf-fb8f-433f-96a8-bebd725673da' },
  { sku:'PJS-022', name:'Myrtillocactus “Stacker” on graft', price:50, detail:'4 in tall · 3.5 in pot', photo:'/api/photo/f2eed56a-82b1-4d08-9d03-98a264904561' },
  { sku:'PJS-013', name:'Astrophytum on tricho graft', price:20, detail:'Josh-grafted exact specimen', photo:'/api/photo/77ef6737-63c1-4d08-8a9f-e0a13e889009' },
  { sku:'PJS-014', name:'Thelocactus hexaedrophorus', price:35, detail:'Flowering specimen · 6 in pot', photo:'/api/photo/0e53121d-35cc-43cd-ba5e-80c8a13e2a61' },
  { sku:'PJS-021', name:'Los Gentiles F2 graft', price:40, detail:'9 in tall · 6 in pot', photo:'/api/photo/962d08ca-c5d6-43eb-9c65-14ad0d1f8b03' },
  { sku:'PJS-020', name:'Noid “Frank”', price:10, detail:'7 in tall · 6 in pot', photo:'/api/photo/3a052c14-e61a-4ad7-9735-c42b91f18127' },
  { sku:'PJS-019', name:'TPM × Psycho0', price:50, detail:'9 in tall · grafted piece', photo:'/api/photo/de475ed6-5ded-4f7c-8c95-8653594f852a' },
  { sku:'PJS-018', name:'Mammillaria uncinata', price:20, detail:'4 in tall · 3.5 in pot', photo:'/api/photo/0ba69aad-5c21-40a1-b2de-50a960cf14d1' },
  { sku:'PJS-016', name:'Echinopsis cv. Chocolate', price:50, detail:'Rarely seen variegated piece', photo:'/api/photo/2219322c-acf6-44fb-b03f-fe97eb874ba2' },
  { sku:'PJS-012', name:'Zorro × Chaco', price:50, detail:'2.5 in tall · 6 in pot', photo:'/api/photo/5ddfd94e-1736-49ed-b60c-44726232590a' }
];

function productCard(product, hidden = false) {
  const article = document.createElement('article');
  article.className = 'mini-product';
  if (hidden) article.hidden = true;
  article.innerHTML = `
    <img src="${photoBase}${product.photo}" alt="${product.name}" loading="lazy">
    <div class="mini-product-copy">
      <div class="mini-meta"><span>${product.sku}</span><span>$${product.price.toFixed(2)}</span></div>
      <h5>${product.name}</h5>
      <p>${product.detail}</p>
      <button class="mini-action" type="button">View details &amp; reserve</button>
    </div>`;
  return article;
}

function inventoryHeader(countLabel) {
  const head = document.createElement('header');
  head.className = 'mini-head';
  head.innerHTML = `<small>Available now</small><h4>On the growing bench.</h4><p>${countLabel}</p>`;
  return head;
}

document.querySelectorAll('[data-inventory-demo]').forEach((screen) => {
  const mode = screen.dataset.inventoryDemo;
  const firstCount = mode === 'six' ? 6 : mode === 'four' ? 4 : products.length;
  screen.append(inventoryHeader(`${products.length} exact specimens · tap a photo for details`));
  products.forEach((product, index) => screen.append(productCard(product, index >= firstCount)));

  if (mode === 'six') {
    const button = document.createElement('button');
    button.className = 'show-more';
    button.type = 'button';
    button.setAttribute('aria-expanded', 'false');
    button.textContent = 'Show 5 more from the bench ↓';
    button.addEventListener('click', () => {
      const opening = button.getAttribute('aria-expanded') === 'false';
      screen.querySelectorAll('.mini-product[hidden]').forEach((card) => { card.hidden = false; });
      if (!opening) {
        [...screen.querySelectorAll('.mini-product')].slice(6).forEach((card) => { card.hidden = true; });
        screen.scrollTo({ top: 0, behavior: 'smooth' });
      }
      button.setAttribute('aria-expanded', String(opening));
      button.textContent = opening ? 'Show fewer plants ↑' : 'Show 5 more from the bench ↓';
    });
    screen.append(button);
    const tail = document.createElement('div');
    tail.className = 'demo-tail';
    tail.innerHTML = '<strong>Meet Josh & the lodge</strong>The story and Lodge Letters arrive sooner.';
    screen.append(tail);
  }

  if (mode === 'four') {
    const button = document.createElement('button');
    button.className = 'full-bench';
    button.type = 'button';
    button.textContent = 'Browse all 11 on the full bench →';
    button.addEventListener('click', () => {
      screen.querySelectorAll('.mini-product[hidden]').forEach((card) => { card.hidden = false; });
      button.remove();
    });
    screen.append(button);
    const tail = document.createElement('div');
    tail.className = 'demo-tail';
    tail.innerHTML = '<strong>Everything below moves up</strong>Fast homepage, separate full collection.';
    screen.append(tail);
  }
});

document.querySelectorAll('[data-backdrop-products]').forEach((screen) => {
  screen.append(inventoryHeader('A customer has been browsing for a while'));
  products.slice(0, Number(screen.dataset.backdropProducts)).forEach((product) => screen.append(productCard(product)));
});

function resetInvite(type) {
  const stage = document.querySelector(`[data-popup-stage="${type}"]`);
  if (!stage) return;
  const invite = stage.querySelector('.email-invite');
  invite.classList.remove('is-expanded');
  invite.classList.add('is-hidden');
  window.setTimeout(() => invite.classList.remove('is-hidden'), 180);
}

document.querySelectorAll('[data-replay]').forEach((button) => {
  button.addEventListener('click', () => resetInvite(button.dataset.replay));
});

document.querySelectorAll('.invite-close,.invite-later').forEach((button) => {
  button.addEventListener('click', () => button.closest('.email-invite').classList.add('is-hidden'));
});

document.querySelectorAll('.bar-open,.pill-open').forEach((button) => {
  button.addEventListener('click', () => button.closest('.email-invite').classList.add('is-expanded'));
});

document.querySelectorAll('.demo-submit').forEach((button) => {
  button.addEventListener('click', () => {
    const invite = button.closest('.email-invite');
    invite.innerHTML = '<div class="demo-success">Demo only — no email was submitted.<br>Thanks for trying it.</div>';
  });
});
