export function initDeskDetails(){
  const dialog=document.querySelector('.artifact-dialog');
  if(!dialog)return;
  let opener;
  const choose=kind=>{
    dialog.querySelectorAll('[data-artifact-panel]').forEach(panel=>{panel.hidden=panel.dataset.artifactPanel!==kind;});
    dialog.querySelectorAll('[data-artifact-tab]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.artifactTab===kind)));
    dialog.querySelector('#artifact-title').textContent=kind==='phone'?'Inside the app.':'Inside the store listing.';
  };
  document.querySelectorAll('[data-artifact-open]').forEach(button=>button.addEventListener('click',()=>{
    opener=button;choose(button.dataset.artifactOpen);dialog.showModal();dialog.scrollTop=0;document.body.style.overflow='hidden';dialog.querySelector('.artifact-close').focus();
  }));
  dialog.querySelectorAll('[data-artifact-tab]').forEach(button=>button.addEventListener('click',()=>choose(button.dataset.artifactTab)));
  dialog.querySelector('.artifact-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();});
  dialog.addEventListener('close',()=>{document.body.style.overflow='';opener?.focus({preventScroll:true});});
  dialog.querySelector('[data-inspect-evidence]').addEventListener('click',()=>{
    dialog.addEventListener('close',()=>{
      document.querySelector('[data-case="screenshots"]').click();
      const heading=document.querySelector('#inspection-heading');heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});heading.scrollIntoView({block:'start',behavior:'instant'});
    },{once:true});dialog.close();
  });
}
