/**
 * structure-versions.js — `?structure=<id>&version=<label>` (T-1727).
 *
 * The owner compares competing builds of one structure side by side on dev — the
 * Glessner House first — by opening the same scene in two tabs with two labels:
 *
 *   /4d/dev/1835/?structure=bates_auction_room&version=fixture
 *   /4d/dev/1835/?structure=bates_auction_room&version=default
 *
 * A version is a committed alternate RECORD plus its own mesh (see
 * generators/common/versions.py and docs/STRUCTURE-VERSIONS.md). The compiler lists
 * each scene's versions in `sidecars/<year>/versions/index.json`, and this module is
 * the only thing that reads it — and it reads it only when the address asks for a
 * version, so a visitor who does not pays nothing: the boot payload is unchanged.
 *
 * What it guarantees, and the smoke holds each one:
 *   - exactly ONE registry entry is swapped: the requested id's sidecar path (and so
 *     its mesh) is replaced by the version's, and nothing else in the scene moves;
 *   - an unknown id or label NEVER fails silently and never blanks the scene — the
 *     default loads and `notice` says, in words, what was asked for and not found;
 *   - `version=default` shows the canonical record WITH the HUD saying so, so two
 *     screenshots of the same corner cannot be confused.
 *
 * Nothing here decides what is documented; the version's sidecar is compiled from its
 * record by tools/compile_scene.py exactly as the default's is (AGENTS.md rule 5).
 */

/** The label rule's SHAPE, restated for the address bar. The whole rule — including the
 *  refusal of any model identifier — is generators/common/versions.py, enforced on the
 *  committed files by tools/validate.py; the browser only refuses to fetch a string that
 *  could not possibly be a committed label. */
export const LABEL_SHAPE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const ID_SHAPE = /^[a-z0-9_]+$/;
export const DEFAULT_LABEL = 'default';

/**
 * What the address asks for, or null when it asks for nothing.
 *
 * `?structure=` alone asks for nothing yet: main.js reserves further query parameters
 * for "a structure to open", and a bare id must stay free for that meaning. `?version=`
 * without `?structure=` IS a request — a malformed one — so it earns a notice.
 */
export function readVersionRequest(search) {
  const params = new URLSearchParams(search);
  const label = params.get('version');
  if (label === null || label.trim() === '') return null;
  return { id: (params.get('structure') ?? '').trim(), label: label.trim() };
}

function nameOf(entries, id) {
  const row = entries.find((e) => e.id === id);
  return row?.name || id;
}

/**
 * Decide which version (if any) replaces which entry.
 *
 * @param {{id: string, label: string} | null} request   readVersionRequest()
 * @param {{year: string, dataBase: URL, entries: {id: string, name?: string}[],
 *          getJSON: (url: URL) => Promise<any>}} ctx
 * @returns {Promise<{requested: object|null, active: object|null, explicitDefault: boolean,
 *                    notice: string|null, available: string[], name: string|null}>}
 *   `active` is the versions-index row to load in place of the default: {id, label,
 *   summary, test_fixture, sidecar, asset}. It is null whenever the default stands.
 */
export async function resolveStructureVersion(request, { year, dataBase, entries, getJSON }) {
  const state = {
    requested: request, active: null, explicitDefault: false, notice: null,
    available: [], name: null,
  };
  if (!request) return state;
  const { id, label } = request;
  if (!id) {
    state.notice = `?version=${label} needs ?structure=<id> beside it — nothing was swapped, `
      + 'the default town is shown.';
    return state;
  }
  if (!ID_SHAPE.test(id) || !entries.some((e) => e.id === id)) {
    state.notice = `No structure “${id}” in the ${year} scene — nothing was swapped, the `
      + 'default town is shown.';
    return state;
  }
  state.name = nameOf(entries, id);
  if (label === DEFAULT_LABEL) {
    state.explicitDefault = true;
    return state;
  }
  if (!LABEL_SHAPE.test(label)) {
    state.notice = `“${label}” is not a version label — showing the default ${state.name}.`;
    return state;
  }
  let index;
  try {
    index = await getJSON(new URL(`sidecars/${year}/versions/index.json`, dataBase));
  } catch (err) {
    state.notice = `The list of versions could not be read (${err.message}) — showing the `
      + `default ${state.name}.`;
    return state;
  }
  const rows = Array.isArray(index?.structures?.[id]) ? index.structures[id] : [];
  state.available = rows.map((r) => r.label);
  const row = rows.find((r) => r.label === label);
  if (!row) {
    state.notice = rows.length
      ? `No version “${label}” of ${state.name} — showing the default. Versions: `
        + `${state.available.join(', ')}.`
      : `${state.name} has no committed versions — showing the default.`;
    return state;
  }
  state.active = { id, ...row };
  return state;
}

/**
 * What the HUD's version chip says, or null when nothing was asked for. One pure
 * function so the smoke can hold the words without booting a second scene.
 */
export function versionBadge(state) {
  if (!state?.requested) return null;
  if (state.active) {
    const fixture = state.active.test_fixture ? ' (test fixture)' : '';
    const name = state.name ?? state.active.id;
    return {
      tone: 'active',
      text: `version ${state.active.label}`,
      title: `${name}: version “${state.active.label}”${fixture}. `
        + `${state.active.summary ?? ''}`.trim(),
      announce: `Showing version “${state.active.label}” of ${name}${fixture}`,
    };
  }
  if (state.explicitDefault) {
    return {
      tone: 'default',
      text: 'version default',
      title: `${state.name}: the default build (the canonical record).`,
      announce: `Showing the default build of ${state.name}`,
    };
  }
  const notice = state.notice ?? '';
  return { tone: 'notice', text: 'default shown', title: notice, announce: notice };
}
