/**
 * Former residents (T-3266): who lived in a 1904 house BEFORE the scene date, the family
 * the house is named for first, and, for a house nobody is listed in on 1 July 1904, why
 * not and who came after. The rows are `former_residents` in the scene's people.json
 * (tools/build_former_residents_1904.py), read from the Blue Book's street and name lists
 * 1890-1910, the 1900 census and the district markers. They are not people in the
 * directory: a former resident is not a 1904 fact, so a row names the editions it was
 * read in and opens no person card.
 *
 * Drawn by Inspect's People tab with that view's own helpers (`el`, `line`, `heading`),
 * so a row looks like the directory's rows and carries the same grade dot.
 */

const ROLE = { 'built for': 'The family it was built for', 'lived here': 'Lived here', 'lived here after': 'Lived here after' };

function row(doc, h, r) {
  const d = h.el(doc, 'div', 'nav-person insp-former');
  d.append(h.line(doc, 'span', 'nav-person-name', r.name, r.grade));
  const role = r.namesake ? 'The family the house is named for' : ROLE[r.role] ?? r.role;
  d.append(h.el(doc, 'span', 'nav-sub', [role, r.seen].filter(Boolean).join(' · ')));
  if (Array.isArray(r.members) && r.members.length > 1) {
    d.append(h.el(doc, 'span', 'nav-sub insp-former-members', r.members.join(', ')));
  }
  return d;
}

/** True when `house` has anything to show. */
export function hasHistory(house) {
  return !!(house && (house.unlisted_on_scene_date || house.former?.length || house.later?.length));
}

/** The People tab's history block for one house, or null. */
export function formerResidentsBlock(doc, house, h) {
  if (!hasHistory(house)) return null;
  const wrap = h.el(doc, 'div', 'insp-former-wrap');
  if (house.unlisted_on_scene_date?.note) {
    const s = h.el(doc, 'section', 'insp-sec');
    s.append(h.heading(doc, 'Nobody listed in 1904'));
    s.append(h.el(doc, 'p', 'nav-sub', house.unlisted_on_scene_date.note));
    wrap.append(s);
  }
  for (const [key, title] of [['former', 'Former residents'], ['later', 'Later residents']]) {
    const list = house[key];
    if (!Array.isArray(list) || !list.length) continue;
    const s = h.el(doc, 'section', 'insp-sec');
    s.append(h.heading(doc, title));
    for (const r of list) s.append(row(doc, h, r));
    wrap.append(s);
  }
  return wrap;
}
