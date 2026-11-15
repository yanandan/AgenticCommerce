export function searchProducts(products, query = '', sport = '', sort = 'relevance') {
  const tokens = query.toLowerCase().match(/[\p{L}\p{N}_]+/gu) || [];
  const ranked = products.filter(p => !sport || p.category === sport).map(p => {
    const fields = [[p.name, 5], [p.category, 3], [p.product_type || "", 3], [p.sport, 3], [p.brand, 2], [p.description, 1]];
    const scores = tokens.map(token => Math.max(0, ...fields.filter(([value]) => value.toLowerCase().includes(token)).map(([, weight]) => weight)));
    return { p, score: scores.reduce((a, b) => a + b, 0), matches: scores.every(n => n > 0) };
  }).filter(x => x.matches);
  ranked.sort((a, b) => {
    if (sort === 'price-asc') return a.p.price_cents - b.p.price_cents || a.p.id.localeCompare(b.p.id);
    if (sort === 'price-desc') return b.p.price_cents - a.p.price_cents || a.p.id.localeCompare(b.p.id);
    if (sort === 'name') return a.p.name.localeCompare(b.p.name) || a.p.id.localeCompare(b.p.id);
    return b.score - a.score || a.p.id.localeCompare(b.p.id);
  });
  return ranked.map(x => x.p);
}
