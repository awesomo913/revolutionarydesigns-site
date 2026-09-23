/* Website inquiries are submitted only by the visitor. Analytics never includes form values. */
document.querySelectorAll('.mobile-menu a').forEach(link=>link.addEventListener('click',()=>link.closest('details').removeAttribute('open')));
const bar=document.getElementById('mobileCta'),actions=document.querySelector('.hero-actions'),contact=document.getElementById('contact');
if(bar&&actions&&contact&&'IntersectionObserver' in window){
  let pastActions=false,atForm=false;
  const apply=()=>{const show=pastActions&&!atForm;bar.hidden=!show;document.body.classList.toggle('has-mobile-cta',show)};
  new IntersectionObserver(entries=>{const entry=entries[0];pastActions=!entry.isIntersecting&&entry.boundingClientRect.bottom<0;apply()}).observe(actions);
  new IntersectionObserver(entries=>{atForm=entries[0].isIntersecting;apply()}).observe(contact);
}
const track=(name,properties)=>{if(window.posthog?.capture)window.posthog.capture(name,properties)};
document.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{
  const href=link.getAttribute('href')||'';
  if(href.startsWith('tel:'))track('website_contact_click',{method:'phone'});
  else if(href.startsWith('mailto:'))track('website_contact_click',{method:'email'});
  else if(href.startsWith('/demos/'))track('website_demo_open',{demo:href.includes('/store/')?'store':'roofing'});
}));
const form=document.getElementById('audit-form');
if(form){
  const status=document.getElementById('af-status'),button=form.querySelector('button[type=submit]');
  const field=name=>form.elements.namedItem(name);
  const setStatus=(text,error=false)=>{status.textContent=text;status.className='form-status'+(error?' is-error':'')};
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(button.disabled)return;
    let problem;
    if(!field('business').value.trim())problem=['business','Please add your business name.'];
    else if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field('email').value.trim()))problem=['email','Please check your email address.'];
    else if(field('site_url').value.trim()&&!field('site_url').validity.valid)problem=['site_url','Please use a complete website address, starting with https://.'];
    if(problem){setStatus(problem[1],true);field(problem[0]).focus();return}
    // The message is optional on the page, but the worker rejects anything under 10 characters.
    const note=field('message').value.trim();
    const message=note.length>=10?note:note?`${note} (short note from the audit form)`:'(No details given. Wants a free audit.)';
    const label=button.innerHTML;button.disabled=true;button.textContent='Sending…';setStatus('Sending your request…');
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);
    try{
      const res=await fetch('https://cactus-email-worker.revodesigns.workers.dev/request',{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'website_audit',business:field('business').value.trim(),site_url:field('site_url').value.trim(),email:field('email').value.trim(),phone:field('phone').value.trim(),message,website:field('website').value,source:'revodesigns-home'})});
      const data=await res.json().catch(error=>{if(controller.signal.aborted)throw error;return {}});
      if(!res.ok||!data.ok)throw new Error('delivery');
      form.innerHTML='<div class="form-done" role="status"><strong>Thanks—that’s with me.</strong><p>I’ll reply within one business day. If it’s urgent, <a href="tel:+15026420012">call (502) 642-0012</a>.</p></div>';
      track('website_audit_result',{status:'sent'});
    }catch(error){setStatus('Sorry—I couldn’t send that just now. Please call (502) 642-0012 or email hello@revolutionarydesigns.io.',true);track('website_audit_result',{status:'failed'})}
    finally{clearTimeout(timer);button.disabled=false;button.innerHTML=label}
  });
}
