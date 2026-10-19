// SPDX-License-Identifier: GPL-3.0-or-later
/** A role card has no directory link, personal biography or fabricated person id. */
export function showHumanRoleCard(card) {
  if (!card) return;
  let dialog = document.getElementById('human-role-card');
  if (!dialog) { dialog = document.createElement('dialog'); dialog.id = 'human-role-card'; document.body.append(dialog); }
  dialog.replaceChildren();
  const title = document.createElement('h2'); title.id = 'human-role-card-title'; title.textContent = card.title;
  dialog.setAttribute('aria-labelledby', title.id);
  const paragraphs = [card.description, `Scene: ${card.scene}. Grade: reconstructed.`, card.basis, `Fallback: ${card.fallbackBasis}`, `Wardrobe: ${card.wardrobeBasis}`]
    .map(text => { const p = document.createElement('p'); p.textContent = text; return p; });
  const close = document.createElement('button'); close.type = 'button'; close.textContent = 'Close'; close.onclick = () => dialog.close();
  dialog.append(title, ...paragraphs, close);
  if (document.pointerLockElement) document.exitPointerLock?.();
  if (!dialog.open) dialog.showModal(); close.focus();
}
