import { searchProducts } from './search.mjs';
const $ = id => document.getElementById(id);
const symbols = {'The Holiday Shop':'🎁','Sports':'🏀','Golf':'⛳','Shoes':'👟','Women':'👚','Men':'👕','Kids':'🎒','Accessories':'🧢','Fan Shop':'🏟️','Exercise & Wellness':'🏋️','Outdoor':'🏕️'};
const tints = ['#edf0e5','#f2ece2','#e8eef0','#efebe6','#e5ede6'];
let products = [], sport = '', query = '', page = 1;
const pageSize = 24;
const money = new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'});
function el(tag, cls, value) { const e = document.createElement(tag); if(cls) e.className = cls; if(value !== undefined) e.textContent = value; return e; }
function chooseSport(value) { sport = value; $('sport').value = value; page = 1; render(); }
function render() {
  const matches = searchProducts(products, query, sport, $('sort').value);
  const pages = Math.max(1, Math.ceil(matches.length / pageSize));
  page = Math.min(page, pages);
  $('result-count').replaceChildren(el('b', '', `${matches.length} products`), document.createTextNode(query ? ` for “${query}”` : sport ? ` in ${sport}` : ' to explore'));
  $('collection-title').textContent = sport ? sport : 'Find something for your everyday.';
  for (const button of $('sport-list').children) { const selected = button.dataset.sport === sport; button.classList.toggle('active', selected); button.setAttribute('aria-pressed', String(selected)); }
  $('grid').replaceChildren();
  for (const p of matches.slice((page - 1) * pageSize, page * pageSize)) {
    const card = el('article','product-card');
    const art = el('div','product-art'); art.style.setProperty('--tint',tints[(Number(p.id.slice(3))-1)%tints.length]);
    const symbol=el('span','sport-art',symbols[p.category] || '✦'); symbol.setAttribute('aria-hidden','true');
    art.append(el('span','sport-label',p.category),symbol,el('span','art-index',p.id));
    const body=el('div','card-body');
    body.append(el('p','card-brand',p.brand),el('h3','',p.name.startsWith(p.brand+' ') ? p.name.slice(p.brand.length+1) : p.name),el('p','card-description',p.description));
    const bottom=el('div','card-bottom');bottom.append(el('span','price',money.format(p.price_cents/100)),el('span','','USD · SYNTHETIC'));body.append(bottom);card.append(art,body);$('grid').append(card);
  }
  $('empty').hidden = matches.length !== 0;
  document.querySelector('.pagination').hidden = matches.length === 0;
  $('page-count').textContent = `Page ${page} of ${pages}`;
  $('previous').disabled = page === 1; $('next').disabled = page === pages;
}
async function load() {
  $('error').hidden = true;
  try {
    const response = await fetch('./products.json');
    if(!response.ok) throw new Error('Catalog unavailable');
    products = await response.json();
    if(!Array.isArray(products) || products.length !== 300) throw new Error('Invalid catalog');
    const categoryResponse = await fetch('./categories.json');
    if (!categoryResponse.ok) throw new Error('Categories unavailable');
    const sports = await categoryResponse.json();
    if (sports.length !== 11 || !sports.every(c => products.some(p => p.category === c))) throw new Error('Invalid categories');
    $('sport-list').replaceChildren();
    $('sport').replaceChildren(new Option('All categories',''));
    for(const value of ['', ...sports]) {
      const count = value ? products.filter(p=>p.category === value).length : products.length;
      const button=el('button','',value || 'All categories'); button.type='button';button.dataset.sport=value;button.append(el('span','',String(count)));button.addEventListener('click',()=>chooseSport(value));$('sport-list').append(button);
      if(value) $('sport').add(new Option(value,value));
    }
    render();
  } catch(error) { $('error').hidden=false;$('result-count').textContent='Catalog unavailable';document.querySelector('.pagination').hidden=true; }
}
$('search-form').addEventListener('submit',event=>{event.preventDefault();query=$('query').value.trim();page=1;render();});
$('query').addEventListener('search',()=>{if(!$('query').value){query='';page=1;render();}});
$('sport').addEventListener('change',event=>chooseSport(event.target.value));
$('sort').addEventListener('change',()=>{page=1;render();});
for(const button of document.querySelectorAll('[data-query]')) button.addEventListener('click',()=>{$('query').value=button.dataset.query;query=button.dataset.query;page=1;render();});
$('reset').addEventListener('click',()=>{query='';sport='';page=1;$('query').value='';$('sport').value='';render();});
$('retry').addEventListener('click',load);
$('previous').addEventListener('click',()=>{page--;render();$('search-form').scrollIntoView({behavior:'smooth',block:'start'});});
$('next').addEventListener('click',()=>{page++;render();$('search-form').scrollIntoView({behavior:'smooth',block:'start'});});
load();
