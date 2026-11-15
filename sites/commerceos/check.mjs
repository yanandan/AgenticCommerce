import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {searchProducts} from './dist/search.mjs';
const catalog=JSON.parse(readFileSync(new URL('./dist/products.json',import.meta.url)));
assert.equal(catalog.length,300);assert.equal(new Set(catalog.map(p=>p.id)).size,300);assert.equal(new Set(catalog.map(p=>p.category)).size,11);
assert.equal(searchProducts(catalog).length,300);
assert(searchProducts(catalog,'  RUNNING shoes  ').length >= 2);
assert.equal(searchProducts(catalog,'unfindable').length,0);
assert.equal(searchProducts(catalog,'','Golf').length,25);
assert.equal(searchProducts(catalog,'!!!').length,300);
const ordered=searchProducts(catalog,'','','price-asc');assert(ordered.every((p,i)=>!i||p.price_cents>=ordered[i-1].price_cents));
console.log('Catalog and search checks passed.');

const categories=JSON.parse(readFileSync(new URL('./dist/categories.json',import.meta.url)));
assert.deepEqual(categories,['The Holiday Shop','Sports','Golf','Shoes','Women','Men','Kids','Accessories','Fan Shop','Exercise & Wellness','Outdoor']);
for(const c of categories){const matches=searchProducts(catalog,'',c);assert.equal(matches.length,c==='Sports'?50:25);assert(matches.every(p=>p.category===c));}
assert.equal(searchProducts(catalog,'hoodie','Women').length,1);
assert.equal(searchProducts(catalog,'gift','The Holiday Shop').length,22);
assert.equal(searchProducts(catalog,'golf','Fan Shop').length,0);
assert.deepEqual(catalog, JSON.parse(readFileSync(new URL('../../commerceos/data/products.json',import.meta.url))));
console.log('All 11 category filters and Python/browser catalog consistency verified.');
