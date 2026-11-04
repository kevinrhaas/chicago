// SPDX-License-Identifier: GPL-3.0-or-later
/** Only these existing scenes have an occupied, named town-transport candidate. */
export function supportsTownTransport(sceneId) {
  return ['1835', '1904'].includes(String(sceneId));
}
