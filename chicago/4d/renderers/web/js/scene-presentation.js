/** Destination-scoped arrival copy. Historical cards cite the existing research layer. */
import { EARLY_ENTRIES } from './loading-early.js';
export function arrivalTitles(year) {
  return ['Preparing your arrival', 'Setting temporal coordinates', 'Establishing the selected scene',
    'Targeting selected year', 'Resolving your destination', `Destination acquired: Chicago, ${year}`,
    `Approaching Chicago, ${year}`, 'Locating your destination'];
}
const glessnerSource = 'glessner_story_of_a_house_1923';
const prairieCards = [
  ['assess', 'source', 'Reading Glessner’s account of the house’s construction', glessnerSource, 'HABS data pages 13–15'],
  ['assess', 'fact', 'The Glessner family moved into the house in December 1887', 'habs_glessner_house_il_1015_data_pages', 'Data page 1'],
  ['collect', 'fact', 'The house was built with unglazed red roof tiles', glessnerSource, 'HABS data pages 13–15'],
  ['collect', 'build', 'Resolving the Glessner House exterior for 1904'],
  ['prepare', 'fact', 'The service entrance was through the great arch on Eighteenth Street', glessnerSource, 'HABS data page 15'],
  ['prepare', 'operational', 'Preparing the Prairie Avenue scene'],
  ['resolve', 'fact', 'The narrow north windows lit corridors along Eighteenth Street', glessnerSource, 'HABS data pages 13–15'],
  ['resolve', 'operational', 'Finding your starting place at Prairie and Eighteenth'],
].map(([phase, kind, text, source, locator], i) => ({ id: `prairie_1904_${i}`, phase, kind, text,
  weight: 1, min_dwell_ms: 2400, ...(source ? { source_ids: [source], locator } : {}) }));
export function scenePresentation(value, targetDate) {
  const year = /^\d{4}$/.test(String(value)) ? Number(value) : 1835;
  const date = /^\d{4}-\d{2}-\d{2}$/.test(targetDate || '') ? targetDate : null;
  const summer = date ? ['06', '07', '08'].includes(date.slice(5, 7)) : [1835, 1904].includes(year);
  const when = `${summer ? 'summer ' : ''}${year}`;
  const dated = date ? new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${date}T12:00:00Z`)) : when;
  return { year,
    arrivalLine: `You have arrived in Chicago, ${when}.`,
    welcomeTitle: `Welcome to Chicago, ${when}.`,
    eyebrow: year === 1835 ? 'A town at the water’s edge' : year === 1904 ? 'Prairie Avenue' : year === 1812 ? 'The first Fort Dearborn' : 'Chicago through time',
    intro: `You are entering a digital reconstruction of ${year === 1904 ? 'Prairie Avenue' : 'Chicago'} as it stood ${date ? 'on' : 'in'} ${dated}, built from the sources listed under Evidence.`,
    entries: year === 1835 ? EARLY_ENTRIES : year === 1904 ? prairieCards :
      ['assess', 'collect', 'prepare', 'resolve'].map(phase => ({ id: `scene_${year}_${phase}`, phase,
        kind: 'operational', text: `Preparing Chicago, ${year}`, weight: 1, min_dwell_ms: 2400 })),
  };
}
