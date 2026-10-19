/** T-2660 — Settings › About › Field log (DESIGN §14 "Measure fun"): the counts this device
 * keeps for itself (js/field-log.js), never sent anywhere, and the key that clears them. */
import { register } from './index.js';

export default register('fieldlog', {
  'title': 'Field log',
  'note': 'Counted on this device only. Nothing is sent anywhere.',
  'row.landed': 'Landings',
  'row.firstInspect': 'Landings with a building inspected',
  'row.time': 'Time to first inspect',
  'row.tab': 'Inspect tabs opened',
  'row.showMe': 'Show me used',
  'row.jauntStarted': 'Jaunts started',
  'row.jauntFinished': 'Jaunts finished',
  'row.tourStep': 'Tour steps reached',
  'row.confidencePreset': 'Confidence view presets chosen',
  'time.none': 'Not yet',
  'time.value': '{time} last time, {quick} of {landed} within 90 s',
  'time.sec': '{s} s',
  'time.min': '{m} min {s} s',
  'clear.line': 'Start the log again',
  'clear': 'Clear',
  'cleared': 'Cleared. Nothing was kept anywhere else.',
});
