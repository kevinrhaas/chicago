// SPDX-License-Identifier: GPL-3.0-or-later
/** Only these existing scenes have an occupied, named town-transport candidate.
 * T-3497: 1812's garrison wagons, led by teamsters on foot. */
export function supportsTownTransport(sceneId) {
  return ['1812', '1835', '1904'].includes(String(sceneId));
}
