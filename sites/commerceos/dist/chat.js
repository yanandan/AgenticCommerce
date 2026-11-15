import { productCard } from './app.js';
const $ = id => document.getElementById(id);
let runtimePromise, busy = false;
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function view(chat) {
  $('shopping-chat').hidden = !chat;
  $('catalog-browse').hidden = chat;
  for (const [id, active] of [['view-chat',chat],['view-browse',!chat]]) {
    $(id).classList.toggle('selected',active);
    $(id).setAttribute('aria-pressed', String(active));
  }
}
$('view-chat').addEventListener('click',()=>view(true));
$('view-browse').addEventListener('click',()=>view(false));
async function getText(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error('Could not load shopping search');
  return response.text();
}
async function getRuntime() {
  if (!runtimePromise) {
    runtimePromise = (async () => {
      const [{ loadPyodide }, catalog, parser, filtering] = await Promise.all([
        import('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs'),
        getText('./products.json'), getText('./python/commerceos/parser.py'),
        getText('./python/commerceos/filtering.py'),
      ]);
      const python = await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/'});
      python.FS.mkdirTree('/app/commerceos');
      python.FS.writeFile('/app/commerceos/__init__.py','');
      python.FS.writeFile('/app/commerceos/parser.py',parser);
      python.FS.writeFile('/app/commerceos/filtering.py',filtering);
      python.globals.set('_catalog_json',catalog);
      await python.runPythonAsync("import sys, json\nsys.path.insert(0, '/app')\nfrom commerceos.parser import shopping_request\n_catalog = json.loads(_catalog_json)");
      return python;
    })().catch(error => { runtimePromise = undefined; throw error; });
  }
  return runtimePromise;
}
function bubble(role, text) {
  const node = element('article',`chat-message ${role}`);
  node.append(element('p','chat-role', role === 'user' ? 'YOU' : 'COMMERCEOS'));
  if (text) node.append(element('p','chat-message-text',text));
  $('chat-history').append(node);
  return node;
}
function recognizedRequest(result) {
  const c = result.constraints;
  return [c.brand,c.category,c.sport,c.width,c.use_case,
    c.max_price_cents === null ? null : `${c.max_price_inclusive ? 'at most' : 'under'} $${(c.max_price_cents/100).toFixed(2)}`
  ].filter(Boolean).join(' ');
}
function reply(result) {
  const node = bubble('assistant');
  node.append(element('h3','', 'Requirements recognized'));
  const list = element('ul','requirement-list');
  for (const requirement of result.recognized) list.append(element('li','',requirement));
  if (!result.recognized.length) list.append(element('li','','None yet.'));
  node.append(list);
  for (const note of result.unverified_requirements) node.append(element('p','unverified',note));
  if (result.status === 'needs_refinement') {
    node.append(element('h3','','Let’s refine your request.'));
    node.append(element('p','chat-message-text','No products are presented as confirmed matches.'));
    for (const note of result.clarifications) node.append(element('p','clarification',note));
    if (result.recognized.length) {
      const refine = element('button','refine-button','Use only recognized requirements');
      refine.type = 'button';
      refine.addEventListener('click',()=>{ $('chat-request').value=recognizedRequest(result);$('chat-request').focus(); });
      node.append(refine,element('p','refine-note','This fills a new request for you to review and send.'));
    }
  } else if (result.total) {
    node.append(element('h3','',`${result.total} products match every recognized requirement.`));
    const grid = element('div','product-grid chat-product-grid');
    for (const product of result.products.slice(0,12)) grid.append(productCard(product));
    node.append(grid);
    if (result.total > 12) node.append(element('p','clarification',`Showing the first 12 of ${result.total} matches. Add requirements to narrow the search.`));
  } else {
    node.append(element('h3','','No products match every requirement.'));
    node.append(element('p','clarification','No filters were relaxed. Try a different complete request.'));
  }
  const details = element('details','request-flow');
  details.append(element('summary','','Request → result data flow'),element('p','','Your message → deterministic Python rules → recognized constraints → shared catalog filters (AND) → matching products.'));
  details.append(element('pre','',JSON.stringify({request:result.message,constraints:result.constraints,
    unverified_requirements:result.unverified_requirements,status:result.status,
    matching_product_ids:result.products.map(p=>p.id)},null,2)));
  node.append(details);
  return node;
}
async function submit(message) {
  message=message.trim();
  if (!message || busy) return;
  busy=true;
  $('chat-send').disabled=true;
  $('chat-clear').disabled=true;
  $('chat-status').textContent='Preparing your shopping search… The first request may take a moment.';
  const userBubble=bubble('user',message);
  userBubble.scrollIntoView({behavior:'smooth',block:'start'});
  try {
    const python=await getRuntime();
    python.globals.set('_message',message);
    const serialized=await python.runPythonAsync('json.dumps(shopping_request(_catalog, _message))');
    reply(JSON.parse(serialized));
    $('chat-request').value='';
    $('chat-status').textContent='Search complete. Refine with a new, complete request below.';
  } catch(error) {
    bubble('assistant','Shopping search could not load. Check your connection and submit again. The catalog browser is still available.');
    $('chat-status').textContent='Shopping search unavailable. Your request was not applied.';
  } finally {
    busy=false;
    $('chat-send').disabled=false;
    $('chat-clear').disabled=false;
  }
}
$('chat-form').addEventListener('submit',event=>{event.preventDefault();submit($('chat-request').value);});
for (const button of document.querySelectorAll('[data-example]')) button.addEventListener('click',()=>{
  if (busy) return;
  $('chat-request').value=button.dataset.example;submit(button.dataset.example);
});
$('chat-clear').addEventListener('click',()=>{
  if (!busy) { $('chat-history').replaceChildren();$('chat-status').textContent='';$('chat-request').value=''; }
});
