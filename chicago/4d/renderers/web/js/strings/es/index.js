/**
 * Spanish (gap analysis item 15). Loaded by ../index.js only while Spanish is the visitor's
 * language; data only, no import of ../index.js (see LANG there).
 *
 *   sections.js   the string table's sections, keyed exactly as the English ones
 *   text.js       whole English strings the page or a module writes itself, and their Spanish
 *   patterns.js   the same for strings with {placeholders}
 *
 * tools/test_strings.mjs holds them to the English: every key one the table has, every
 * placeholder kept. A string none of them holds reads in English.
 */
import sections from './sections.js';
import text from './text.js';
import patterns from './patterns.js';

export default { sections, text, patterns };
