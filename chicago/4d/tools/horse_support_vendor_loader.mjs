// SPDX-License-Identifier: GPL-3.0-or-later
// Native repository vendor mapping for the bounded CPU-only support re-reader.
import { readFile } from 'node:fs/promises';
const root = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url);
export async function resolve(specifier, context, next) {
  if (specifier === 'three') return { url: new URL('three.module.js', root).href, shortCircuit: true };
  if (specifier.startsWith('three/addons/')) return { url: new URL('addons/' + specifier.slice(13), root).href, shortCircuit: true };
  return next(specifier, context);
}
export async function load(url, context, next) {
  if (url.startsWith(root.href) && url.endsWith('.js')) return { format: 'module', source: await readFile(new URL(url), 'utf8'), shortCircuit: true };
  return next(url, context);
}
