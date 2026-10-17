/**
 * The Navigator's apps (T-2618), in one list so the device can register them all at boot.
 * Each app is its own file and its lane's to change; the list itself changes only when an
 * app is added or retired. Ten is the rail's ceiling (DESIGN §06).
 */
import home from './home.js';
import jaunts from './jaunts.js';
import inspect from './inspect.js';
import people from './people.js';
import map from './map.js';
import confidence from './confidence.js';
import move from './move.js';
import jump from './jump.js';
import guide from './guide.js';
import settings from './settings.js';

export const APPS = [home, jaunts, inspect, people, map, confidence, move, jump, guide, settings];
