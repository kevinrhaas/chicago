/**
 * T-3798: the launch page's System check, as plain words. The page measures this computer
 * with the town's own profile (../js/device-profile.js: graphics, cores, memory and a short
 * draw test), then this module turns the reading into one verdict and one piece of advice.
 * Pure functions only, so tools/test_launch_page.mjs can hold every case.
 *
 * The verdict never promises more than the town will do: the detail it names is the one the
 * town itself boots at on this device (profile.choice.detail), unless the player picked one.
 */

export const DETAIL_WORD = Object.freeze({ full: 'Full', balanced: 'Balanced', light: 'Light' });

/** Cloud play needs a steady link; below this the stream breaks up (about 8 Mbps at 1080p). */
export const CLOUD_MIN_MBPS = 10;
/** Below this the first load of a year is slow enough to say so. */
export const SLOW_MBPS = 5;

/** "ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00009BC5) Direct3D11 …)" → "Intel UHD Graphics 630". */
export function gpuWords(renderer) {
  let s = String(renderer || '');
  const angle = s.match(/^ANGLE \((.*)\)$/);
  if (angle) { const parts = angle[1].split(', '); s = parts[1] || parts[0]; }
  s = s.replace(/^ANGLE Metal Renderer:\s*/, '').replace(/\s*\(0x[0-9a-f]+\)/gi, '')
    .replace(/\s+Direct3D.*$/i, '').replace(/\/PCIe\/SSE2/i, '').replace(/\((R|TM)\)/gi, '').replace(/\s{2,}/g, ' ').trim();
  if (!s) return 'not reported';
  return s.length > 34 ? `${s.slice(0, 33)}…` : s;
}

/** A measured download speed in plain words. */
export function networkWords(mbps) {
  if (!Number.isFinite(mbps) || mbps <= 0) return 'not measured';
  if (mbps >= 100) return `${Math.round(mbps / 10) * 10}+ Mbps · fast`;
  const n = mbps >= 10 ? Math.round(mbps) : Math.round(mbps * 10) / 10;
  return `${n} Mbps · ${mbps >= 25 ? 'fast' : mbps >= SLOW_MBPS ? 'fine' : 'slow'}`;
}

/**
 * One verdict for this computer.
 *   reading: { score, grade, detail, webgl2, software, touch, mbps }  (software: no graphics chip in use)
 *   cloud:   { offered, ready }  offered = this player may use cloud play;
 *                                ready   = the cloud machines are running for players yet
 *   chosen:  the Scene detail the player picked ('' when they left it automatic)
 * Returns { kind, title, advice, detail, cloud } where kind is one of
 *   'ready'  plays well here           'lower'  plays here at reduced detail
 *   'cloud'  cloud play is the better way      'blocked' this browser cannot draw the town
 * and `cloud` says whether to put the cloud button forward.
 */
export function verdictFor(reading = {}, cloud = {}, chosen = '') {
  const { score = 0, grade = 'fair', detail = 'full', webgl2 = true, mbps = NaN } = reading;
  const canStream = !!cloud.offered && (!Number.isFinite(mbps) || mbps >= CLOUD_MIN_MBPS);
  const streamWord = cloud.ready ? 'Play from the cloud' : 'Cloud play (opening soon)';
  const slow = Number.isFinite(mbps) && mbps < SLOW_MBPS ? ' Your connection is slow, so the first load will take a while.' : '';
  const level = DETAIL_WORD[chosen] || DETAIL_WORD[detail] || 'Full';
  const pick = chosen && DETAIL_WORD[chosen] ? ` You chose ${level} detail in Settings.` : '';
  if (!webgl2) {
    return { kind: 'blocked', detail: '', cloud: canStream, title: 'This browser cannot draw the town',
      advice: canStream ? `${streamWord} instead, or open this page in an up-to-date Chrome, Edge, Firefox or Safari.`
        : 'Open this page in an up-to-date Chrome, Edge, Firefox or Safari.' };
  }
  // Software drawing (Chrome or Edge with hardware acceleration off, or no driver): the draw
  // test can still score well on a fast processor, but the town will not run smoothly.
  if (reading.software) {
    return { kind: canStream ? 'cloud' : 'lower', detail: chosen || 'light', cloud: canStream,
      title: canStream ? 'Cloud play recommended' : `Playable at ${DETAIL_WORD[chosen] || 'Light'} detail`,
      advice: 'This browser is drawing without the graphics chip. Turn on hardware acceleration in its settings (Chrome and Edge: Settings › System), then check again.'
        + (canStream ? ` Or ${streamWord.toLowerCase()}.` : '') + pick + slow };
  }
  if (grade === 'poor' || score < 20) {
    return { kind: canStream ? 'cloud' : 'lower', detail: chosen || 'light', cloud: canStream,
      title: canStream ? 'Cloud play recommended' : `Playable at ${DETAIL_WORD[chosen] || 'Light'} detail`,
      advice: (canStream ? `This computer will struggle with the town. ${streamWord} runs it on our machine and looks much better.`
        : 'This computer will struggle with the town. Close other tabs and apps before you play.') + pick + slow };
  }
  if (grade === 'low' || score < 40) {
    return { kind: 'lower', detail: chosen || detail, cloud: canStream, title: `Playable here · ${level} detail`,
      advice: `The town opens at ${level} detail here: every street, building and person, drawn more simply.`
        + (canStream ? ` ${streamWord} would look sharper.` : '') + pick + slow };
  }
  return { kind: 'ready', detail: chosen || detail, cloud: false, title: `Ready · ${level} detail`,
    advice: (grade === 'peak' ? 'This computer runs the town at its best. Play here.' : 'This computer runs the town well. Play here.') + pick + slow };
}

/** The rows of the check, as label → words. `shared`: device-profile.js sharesSystemMemory, on a computer. */
export function checkRows(profile = {}, { mbps = NaN, shared = false } = {}) {
  const s = profile.signals || {};
  const software = /software rasteriser/.test(profile.why || '');
  return {
    gpu: !s.webgl2 && !s.renderer ? 'no 3D drawing in this browser' : software ? 'software drawing (no graphics chip in use)' : gpuWords(s.renderer)
      + (shared ? ' · shares system memory' : ''),
    cpu: s.cores ? `${s.cores} cores` : 'not reported',
    memory: s.memoryGB ? `${s.memoryGB >= 8 ? '8+' : s.memoryGB} GB` : 'not reported by this browser',
    network: networkWords(mbps),
  };
}
