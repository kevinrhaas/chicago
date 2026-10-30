/**
 * People (SCR 04) as its own screen, loaded the first time it opens (T-2618).
 *
 * Used where a scene has a people directory but not the drawer's People section: 1904,
 * whose directory (`sidecars/1904/people.json`, T-2702) is the Glessner household and
 * which deliberately lists no `residents` layer (T-1740 keeps the drawer's People, City,
 * Population and Order book on 1835's files). The directory is fetched here, on first
 * open, never at boot. Each person names their household, their place in it and the
 * grade of the record; a tap opens their own card on the house they live in (T-3265).
 */
const RANK = { head: 0, wife: 1, husband: 1, son: 2, daughter: 2, child: 2, servant: 4 };
const GRADES = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const PLACE = { head: 'Head of the household', wife: 'Wife', husband: 'Husband', son: 'Son', daughter: 'Daughter' };
const placeIn = (r) => PLACE[r] ?? (r ? r.charAt(0).toUpperCase() + r.slice(1).replace(/_/g, ' ') : '');

export async function mount(el, ctx = {}) {
  const doc = el.ownerDocument;
  el.replaceChildren(Object.assign(doc.createElement('p'), { className: 'nav-sub', textContent: 'Reading the directory…' }));
  let dir = null;
  try { dir = await ctx.actions?.peopleDirectory?.(); } catch { dir = null; }
  el.replaceChildren();
  const rows = dir?.people ?? [];
  if (!rows.length) {
    el.append(Object.assign(doc.createElement('p'), { className: 'nav-sub', textContent: 'The people directory for this scene could not be read.' }));
    return;
  }
  const byHouse = new Map();
  for (const p of rows) {
    const key = p.household_name || 'A household';
    if (!byHouse.has(key)) byHouse.set(key, []);
    byHouse.get(key).push(p);
  }
  for (const [house, people] of byHouse) {
    const block = Object.assign(doc.createElement('section'), { className: 'nav-block' });
    block.append(Object.assign(doc.createElement('span'), { className: 'nav-k', textContent: 'Household' }),
      Object.assign(doc.createElement('strong'), { className: 'nav-place', textContent: house }));
    // T-3258: the family before its staff — head, spouse, children, kin, then the servants the
    // 1900 census names — so a house of twelve servants still opens on the people it is named for.
    const order = (p) => RANK[p.relationship] ?? 3;
    for (const p of [...people].sort((a, b) => order(a) - order(b) || a.name.localeCompare(b.name))) {
      const row = doc.createElement(p.lives_at ? 'button' : 'div');
      row.className = 'nav-person';
      if (p.lives_at) {
        row.type = 'button';
        // T-3022: the house opens in Inspect, whose Back returns here; T-3265: on the People
        // tab, with this person's own card open.
        row.addEventListener('click', () => {
          if (ctx.actions?.openPerson) void ctx.actions.openPerson(p.id);
          else ctx.actions?.inspect?.(p.lives_at);
        });
      }
      const name = Object.assign(doc.createElement('span'), { className: 'nav-person-name', textContent: p.name });
      const sub = Object.assign(doc.createElement('span'), { className: 'nav-sub',
        textContent: [placeIn(p.relationship), GRADES[p.grade]].filter(Boolean).join(' · ') });
      row.append(name, sub);
      block.append(row);
    }
    el.append(block);
  }
}

export function unmount(el) { el.replaceChildren(); }
