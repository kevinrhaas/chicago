// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import { createTownTransport } from './town-transport.js';
import { supportsTownTransport } from './transport-loop.js';
import { createTransportClearance, giveRoomStand } from './transport-clearance.js';
import { teamSupportAt, certifiedHorseSupportDomain } from './transport-support.js';
import { registerTransportInteractions } from './transport-interactions.js';

/** Small scene binding; the first occupied GLB and whole-route reading stay lazy. */
export async function mountTownTransport({ sceneId, dataBase, people, getPeople = null, preparePersonCard = null, humans, confidence,
  heightAt, footprints, visitor, interactions, detail, coarse = false, problems = [],
  blockedAt = () => false, placeVisitor = null, configFile = 'transport/driven/loops.json' }) {
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
  // Light/remote boot needs route metadata, never assembly modules or loaders.
  // Start these only for an ordinary eligible assembly, alongside its directory.
  let assemblyModules = null, assemblyTools = null;
  const prepareAssemblyModules = () => (assemblyModules ??= Promise.all([
    import('./driven-assembly-loader.js'), import('./draft-hitch.js'),
    import('three/addons/loaders/GLTFLoader.js'), import('./horse-appearance.js'),
  ]).catch(error => { assemblyModules = null; throw error; }));
  const getAssemblyTools = () => (assemblyTools ??= prepareAssemblyModules()
    .then(async ([{ createDrivenAssemblyLoader }, { createDraftHitchFactory }, { GLTFLoader }, { loadHorseRecipe }]) => {
    const loader = new GLTFLoader();
    return { createDrivenAssemblyLoader, coatRecipe: config.horse_appearance
      ? await loadHorseRecipe(dataBase, config.horse_appearance.recipe_file) : null, makeHitch: createDraftHitchFactory({ confidence, loadJSON: json,
      loadGLTF: file => loader.loadAsync(new URL(file, moduleBase).href) }) };
  }).catch(error => { assemblyTools = null; throw error; }));
  const makeByHorse = new Map(), live = new Map(), fixed = new Map();
  /** T-3475: Step back. The road the stopped team will drive next (GIVE_ROOM_AHEAD_M of it,
   *  from where it stands), and the nearest stand beside it the visitor can walk to. */
  const GIVE_ROOM_AHEAD_M = 30;
  const giveRoomFor = row => ({
    plan(actor) {
      const person = visitor();
      if (!person || person.flying) return null;
      const from = actor.snapshot().distance_m, poses = [];
      try {
        for (let s = 0; s <= GIVE_ROOM_AHEAD_M; s += .25) poses.push(actor.previewAt(from + s));
      } catch { return null; }
      // Stepping aside helps only when the visitor is what holds it: the road itself is clear.
      const road = clearance(fixed, row, false);
      if (!road(poses[0], poses[1])) return null;
      const to = giveRoomStand({ poses, envelope_local_xz_m: row.envelope_local_xz_m,
        at: { e: person.e, n: person.n }, blockedAt });
      return to ? { from: { e: person.e, n: person.n }, to } : null;
    },
    place: (e, n) => placeVisitor(e, n),
  });
  let registration = null, town;
  const clearance = (cache, row, includeVisitor) => {
    if (!cache.has(row.id)) cache.set(row.id, createTransportClearance({ footprints,
      visitor: includeVisitor ? visitor : () => null,
      envelope_local_xz_m: row.envelope_local_xz_m }));
    return cache.get(row.id);
  };
  town = createTownTransport({ rows, sceneId, heightAt, detail, problems,
    prepareAssembly(row) {
      const modules = prepareAssemblyModules();
      // Optional scene UI preparation is metadata-only and cannot block assembly.
      try { Promise.resolve(preparePersonCard?.(row.person_id)).catch(() => {}); } catch { /* the real card route remains authoritative */ }
      return modules;
    },
    clear: (row, a, b) => clearance(live, row, true)(a, b),
    routeClear: (row, a, b) => clearance(fixed, row, false)(a, b),
    routeSupport: (row, pose) => teamSupportAt(row, pose, heightAt, supportByHorse.get(modelFor(row))),
    async makeAssembly(row) {
      const model = modelFor(row);
      // Lazy eligible assembly only: Light/remote boot never fetches a district directory.
      const [directory, { createDrivenAssemblyLoader, makeHitch, coatRecipe }] = await Promise.all([
        Array.isArray(people?.people) ? people : getPeople?.(), getAssemblyTools(),
      ]);
      if (!Array.isArray(directory?.people)) throw Error('town transport: this scene named people directory is unavailable');
      if (!makeByHorse.has(model)) makeByHorse.set(model, createDrivenAssemblyLoader({
        sceneId, people: directory.people, profiles: config.profiles ?? [],
        humanAssets: humans.assets, confidence, heightAt, horseSpec: config.horse_models[model], horseSupportDomain: supportByHorse.get(model),
        makeHitch, coatRecipe, driverLod: coarse ? 3 : 0,
        // T-3497: a teamster on foot is the scene's own figure of him, made as the layer makes it.
        createWalker: typeof humans.createActor === 'function'
          ? (instance, identity) => humans.createActor(instance, { person: identity.person, identity }) : null,
        adoptPerson(instance, actor) {
          if (instance.person_id !== actor.personId) throw Error('town transport: driver identity mismatch');
          return humans.withhold(instance.person_id, { instanceId: instance.id, externalActor: actor });
        },
      }));
      // T-3497: phones and Light take a row's lighter level of the same vehicle, when it has one.
      return makeByHorse.get(model)(coarse && row.vehicle_file_light
        ? { ...row, vehicle_file: row.vehicle_file_light, vehicle_glb_sha256: row.vehicle_glb_sha256_light } : row);
    },
    onActorsChanged(actors) {
      registration?.dispose();
      registration = registerTransportInteractions(interactions, actors, actor => {
        const row = rows.find(r => r.id === actor.id);
        return { vehicle: /brougham|carriage/i.test(`${row?.vehicle_file ?? ''} ${row?.name ?? ''}`) ? 'carriage' : 'wagon',
          giveRoom: row && placeVisitor ? giveRoomFor(row) : null };
      });
      if (town.roots.length) group.add(...town.roots);
    },
  });
  const dispose = town.dispose;
  return Object.assign(town, { group,
    refreshInteractions() { registration?.refresh(); },
    dispose() { registration?.dispose(); registration = null; dispose(); group.removeFromParent(); },
  });
}
