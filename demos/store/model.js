(function(root){
  const products=Object.freeze({mug:{name:'Ivory mug',price:2400},bowls:{name:'Sand bowl set',price:3800},linen:{name:'Linen tea towel',price:1800}});
  function normalize(value){const cart={};if(value&&typeof value==='object'&&!Array.isArray(value))for(const id of Object.keys(products)){const qty=value[id];if(Number.isInteger(qty)&&qty>0)cart[id]=Math.min(qty,10)}return cart}
  function change(value,id,delta){const cart=normalize(value);if(!products[id]||!Number.isInteger(delta))return cart;const qty=Math.max(0,Math.min(10,(cart[id]||0)+delta));if(qty)cart[id]=qty;else delete cart[id];return cart}
  function totals(value,mode){const cart=normalize(value),count=Object.values(cart).reduce((a,b)=>a+b,0),subtotal=Object.entries(cart).reduce((sum,[id,qty])=>sum+products[id].price*qty,0),shipping=count&&mode==='delivery'?900:0;return {count,subtotal,shipping,total:subtotal+shipping}}
  const api={products,normalize,change,totals};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.StoreModel=api;
})(typeof window!=='undefined'?window:globalThis);
