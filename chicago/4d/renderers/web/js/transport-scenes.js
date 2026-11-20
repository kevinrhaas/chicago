// SPDX-License-Identifier: GPL-3.0-or-later
/** Only these existing scenes have an occupied, named town-transport candidate.
 * T-3497: 1812's garrison wagons, led by teamsters on foot. T-3690: 1871's Sunday wagons. */
export function supportsTownTransport(sceneId) {
  return ['1812', '1835', '1871', '1904'].includes(String(sceneId));
}
