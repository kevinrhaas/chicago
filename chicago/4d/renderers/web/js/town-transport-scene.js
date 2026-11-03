// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createTownTransport } from './town-transport.js';
import { supportsTownTransport } from './transport-loop.js';
import { createDrivenAssemblyLoader } from './driven-assembly-loader.js';
import { createDraftHitchFactory } from './draft-hitch.js';
import { createTransportClearance } from './transport-clearance.js';
import { teamSupportAt, certifiedHorseSupportDomain } from './transport-support.js';
import { registerTransportInteractions } from './transport-interactions.js';

/** Small scene binding; the first occupied GLB and whole-route reading stay lazy. */
export async function mountTownTransport({ sceneId, dataBase, people, getPeople = null, humans, confidence,
  heightAt, footprints, visitor, interactions, detail, coarse = false, problems = [],
  configFile = 'transport/driven/loops.json' }) {
  if (!supportsTownTransport(sceneId)) return null;
  sceneId = String(sceneId);
  const json = async (file, expectedSHA256 = null) => {
    const response = await fetch(new URL(file, dataBase));
    if (!response.ok) throw Error(`town transport ${file}: HTTP${response.status}`);
    if (!expectedSHA256) return response.json();
    const bytes = await response.arrayBuffer();
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
      .map(n => n.toString(16).padStart(2, '0')).join('');
    if (hash !== expectedSHA256) throw Error('town transport: support certificate bytes differ');
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  const config = await json(configFile);
  const supportByHorse = new Map();
  for (const [model, spec] of Object.entries(config.horse_models)) {
    if (spec.support_domain) {
      const cert = await json(spec.support_domain.certificate_file, spec.support_domain.certificate_sha256);
      supportByHorse.set(model, certifiedHorseSupportDomain(spec, cert));
    }
  }
  const modelFor = row => coarse && row.horse_model_light ? row.horse_model_light : row.horse_model;
  const rows = config.rows.filter(row => row.scene === sceneId);
  const group = new THREE.Group(); group.name = 'town-transport';
  const moduleBase = new URL('../', import.meta.url);
  const loader = new GLTFLoader();
  const makeHitch = createDraftHitchFactory({ confidence, loadJSON: json,
    loadGLTF: file => loader.loadAsync(new URL(file, moduleBase).href) });
  const makeByHorse = new Map(), live = new Map(), fixed = new Map();
  let registration = null, town;
  const clearance = (cache, row, includeVisitor) => {
    if (!cache.has(row.id)) cache.set(row.id, createTransportClearance({ footprints,
      visitor: includeVisitor ? visitor : () => null,
      envelope_local_xz_m: row.envelope_local_xz_m }));
    return cache.get(row.id);
  };
  town = createTownTransport({ rows, sceneId, heightAt, detail, problems,
    clear: (row, a, b) => clearance(live, row, true)(a, b),
    routeClear: (row, a, b) => clearance(fixed, row, false)(a, b),
    routeSupport: (row, pose) => teamSupportAt(row, pose, heightAt, supportByHorse.get(modelFor(row))),
    async makeAssembly(row) {
      const model = modelFor(row);
      // Lazy eligible assembly only: Light/remote boot never fetches a district directory.
      const directory = Array.isArray(people?.people) ? people : await getPeople?.();
      if (!Array.isArray(directory?.people)) throw Error('town transport: this scene named people directory is unavailable');
      if (!makeByHorse.has(model)) makeByHorse.set(model, createDrivenAssemblyLoader({
        sceneId, people: directory.people, profiles: config.profiles ?? [],
        humanAssets: humans.assets, confidence, heightAt, horseSpec: config.horse_models[model], horseSupportDomain: supportByHorse.get(model),
        makeHitch, driverLod: coarse ? 3 : 0,
        adoptPerson(instance, actor) {
          if (instance.person_id !== actor.personId) throw Error('town transport: driver identity mismatch');
          return humans.withhold(instance.person_id, { instanceId: instance.id, externalActor: actor });
        },
      }));
      return makeByHorse.get(model)(row);
    },
    onActorsChanged(actors) {
      registration?.dispose();
      registration = registerTransportInteractions(interactions, actors);
      group.add(...town.roots);
    },
  });
  const dispose = town.dispose;
  return Object.assign(town, { group,
    refreshInteractions() { registration?.refresh(); },
    dispose() { registration?.dispose(); registration = null; dispose(); group.removeFromParent(); },
  });
}
