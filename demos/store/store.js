/* This demonstration never creates a network request, payment, or real order. */
const model=window.StoreModel,key='revodesigns-field-form-demo-cart';
let cart={};try{cart=model.normalize(JSON.parse(localStorage.getItem(key)||'{}'))}catch(error){}
const items=document.getElementById('cart-items'),delivery=document.getElementById('delivery'),checkout=document.getElementById('checkout'),confirmation=document.getElementById('order-confirmation'),status=document.getElementById('shop-status');
const money=cents=>'$'+(cents/100).toFixed(2);
const save=()=>{try{localStorage.setItem(key,JSON.stringify(cart))}catch(error){}};
function render(){
  const total=model.totals(cart,delivery.value);document.getElementById('cart-count').textContent='('+total.count+')';
  items.innerHTML=Object.entries(cart).map(([id,qty])=>`<div class="cart-row"><strong>${model.products[id].name}</strong><p>${money(model.products[id].price)} each · ${money(model.products[id].price*qty)}</p><div class="quantity"><button data-change="${id}" data-delta="-1" aria-label="Decrease ${model.products[id].name} quantity">−</button><span aria-label="${qty} items">${qty}</span><button data-change="${id}" data-delta="1" aria-label="Increase ${model.products[id].name} quantity" ${qty>=10?'disabled':''}>+</button><button class="remove" data-remove="${id}" aria-label="Remove ${model.products[id].name}">Remove</button></div></div>`).join('')||'<p class="cart-note">Your bag is empty. Add something from the collection to try the checkout.</p>';
  document.getElementById('cart-totals').innerHTML=`<div><span>Subtotal</span><span>${money(total.subtotal)}</span></div><div><span>${delivery.value==='delivery'?'Sample delivery':'Sample pickup'}</span><span>${money(total.shipping)}</span></div><div class="total"><span>Sample total</span><span>${money(total.total)}</span></div>`;
  checkout.disabled=!total.count;
}
const resetConfirmation=()=>{confirmation.hidden=true;confirmation.innerHTML='';checkout.textContent='Continue to sample checkout';checkout.dataset.stage='cart'};
document.querySelectorAll('[data-add]').forEach(button=>button.addEventListener('click',()=>{const id=button.dataset.add;const before=cart[id]||0;cart=model.change(cart,id,1);save();resetConfirmation();render();status.textContent=(cart[id]||0)>before?model.products[id].name+' added to your bag.':'Demo limit: 10 of each item.'}));
items.addEventListener('click',event=>{const button=event.target.closest('button');if(!button)return;if(button.dataset.remove){delete cart[button.dataset.remove]}else if(button.dataset.change){cart=model.change(cart,button.dataset.change,Number(button.dataset.delta))}save();resetConfirmation();render();status.textContent='Your sample bag has been updated.'});
delivery.addEventListener('change',()=>{resetConfirmation();render()});
document.getElementById('reset-cart').addEventListener('click',()=>{cart={};delivery.value='pickup';save();resetConfirmation();render();status.textContent='Sample cart reset.'});
checkout.addEventListener('click',()=>{
  const total=model.totals(cart,delivery.value);if(!total.count)return;
  if(checkout.dataset.stage!=='confirm'){
    confirmation.hidden=false;confirmation.className='order-done';confirmation.innerHTML='<h3>Review the sample order.</h3><p>'+total.count+' item'+(total.count===1?'':'s')+' · '+money(total.total)+' · '+(delivery.value==='delivery'?'Sample delivery':'Sample pickup')+'</p><p>No money is charged, no personal information is collected, and no order is sent.</p>';checkout.textContent='Place browser-only sample order';checkout.dataset.stage='confirm';
  }else{
    const summary=Object.entries(cart).map(([id,qty])=>qty+' × '+model.products[id].name).join(', ');cart={};save();render();checkout.textContent='Continue to sample checkout';checkout.dataset.stage='cart';confirmation.innerHTML='<h3>Sample order complete.</h3><p>'+summary+'</p><p>Sample total: '+money(total.total)+'. Nothing was charged or sent. Add a product to try again.</p>';confirmation.hidden=false;confirmation.className='order-done';confirmation.setAttribute('role','status');confirmation.tabIndex=-1;confirmation.focus();status.textContent='Browser-only sample order complete.';
  }
});
render();
