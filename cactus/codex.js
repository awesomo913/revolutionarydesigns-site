const search=document.querySelector('#codex-search');
const region=document.querySelector('#codex-region');
if(search&&region){
  const sections=[...document.querySelectorAll('.codex-regions>section')];
  const cards=[...document.querySelectorAll('.codex-regions .card')];
  function filter(){
    const terms=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    for(const section of sections){
      const inRegion=!region.value||section.id===region.value;
      for(const card of section.querySelectorAll('.card'))card.hidden=!inRegion||!terms.every(term=>card.textContent.toLowerCase().includes(term));
      section.hidden=![...section.querySelectorAll('.card')].some(card=>!card.hidden);
    }
    const visible=cards.filter(card=>!card.hidden);
    const profiles=new Set(visible.map(card=>card.getAttribute('href'))).size;
    document.querySelector('#codex-result-count').textContent=`${profiles} plant profiles · ${visible.length} entries across the collection`;
    document.querySelector('#codex-empty').hidden=visible.length>0;
  }
  search.addEventListener('input',filter);region.addEventListener('change',filter);filter();
}
document.querySelectorAll('.root-card[onclick]').forEach(card=>{
  card.tabIndex=0;card.setAttribute('role','button');
  card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();card.click();}});
});
