const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('js/services.js','utf8');
function setup(response){
  let submit,timer,requests=0;
  const fields={business:{value:'Sample business',focus(){}},email:{value:'sample@example.com',focus(){}},phone:{value:'',focus(){}},site_url:{value:'',validity:{valid:true},focus(){}},message:{value:'More inspection requests',focus(){}},website:{value:''}};
  const button={disabled:false,innerHTML:'Send request',textContent:''},status={textContent:'',className:''};
  const form={elements:{namedItem:name=>fields[name]},innerHTML:'',querySelector:()=>button,addEventListener:(name,handler)=>submit=handler};
  const context={window:{},document:{querySelectorAll:()=>[],querySelector:()=>null,getElementById:id=>id==='audit-form'?form:id==='af-status'?status:null},AbortController,setTimeout:callback=>{timer=callback;return 1},clearTimeout:()=>{},fetch:async(...args)=>{requests++;return response(...args)}};
  vm.runInNewContext(source,context);
  return {fields,button,status,form,send:()=>submit({preventDefault(){}}),timeout:()=>timer(),requests:()=>requests};
}
(async()=>{
  let submitted;
  let test=setup(async(url,options)=>{submitted=JSON.parse(options.body);return {ok:true,json:async()=>({ok:true})}});
  await test.send();assert.match(test.form.innerHTML,/Thanks/);assert.equal(submitted.kind,'website_audit');assert.equal(test.button.disabled,false);
  test=setup(async()=>({ok:false,json:async()=>({error:'rejected'})}));await test.send();assert.match(test.status.textContent,/502/);assert.equal(test.button.disabled,false);
  test=setup(async()=>{throw Error('offline')});await test.send();assert.match(test.status.textContent,/couldn’t send/);assert.equal(test.button.innerHTML,'Send request');
  test=setup(async()=>{throw Error('must not submit')});test.fields.business.value='';await test.send();assert.equal(test.requests(),0);assert.match(test.status.textContent,/business name/);
  test=setup(async()=>{throw Error('must not submit')});test.fields.site_url.value='bad url';test.fields.site_url.validity.valid=false;await test.send();assert.equal(test.requests(),0);assert.match(test.status.textContent,/https/);
  test=setup(async(url,options)=>({ok:true,json:()=>new Promise((resolve,reject)=>{if(options.signal.aborted)reject(Error('aborted'));else options.signal.addEventListener('abort',()=>reject(Error('aborted')),{once:true})})}));
  const pending=test.send();await new Promise(setImmediate);test.timeout();await pending;assert.equal(test.button.disabled,false);assert.match(test.status.textContent,/couldn’t send/);
  console.log('Website inquiry: validation, delivery success, rejection, offline and stalled response-body timeout passed; no real requests sent.');
})().catch(error=>{console.error(error);process.exitCode=1});
