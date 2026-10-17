/**
 * portable-math.js — sin, cos, atan2 and acos that give the same bits in every
 * JavaScript engine (T-2703).
 *
 * `Math.sin`, `Math.cos`, `Math.atan2`, `Math.acos`, `Math.exp` and `Math.pow`
 * are only specified to be close to the true value, and engines differ in the
 * last bit. Measured 2026-10-17 over 200,000 arguments each, Node 22's V8 and
 * Chromium 156's disagreed on atan2 for 35,520 of them, cos for 6,834, sin for
 * 6,699 and acos for 15,352; `Math.sqrt`, `Math.hypot` and plain arithmetic
 * agreed everywhere. So a layer whose geometry runs through those functions
 * cannot be built at publish in Node and match the page byte for byte, and the
 * page itself lays different bits in Safari than in Chrome.
 *
 * These are the FreeBSD msun kernels (from Sun's fdlibm), written only with
 * + - * / and Math.sqrt, which IEEE 754 rounds exactly and JavaScript may not
 * fuse. They agree with Math to within an ulp or two, which is far below
 * anything a vertex in float32 can hold, and with each other everywhere. The
 * argument reduction is two-part Cody-Waite, exact enough for the |x| < 1e5 a
 * turn angle or a bearing can be.
 */

const PIO2_1 = 1.57079632673412561417e+00;   // the first 33 bits of pi/2
const PIO2_1T = 6.07710050650619224932e-11;  // pi/2 - PIO2_1
const INV_PIO2 = 6.36619772367581382433e-01;

const S1 = -1.66666666666666324348e-01;
const S2 = 8.33333333332248946124e-03;
const S3 = -1.98412698298579493134e-04;
const S4 = 2.75573137070700676789e-06;
const S5 = -2.50507602534068634195e-08;
const S6 = 1.58969099521155010221e-10;

const C1 = 4.16666666666666019037e-02;
const C2 = -1.38888888888741095749e-03;
const C3 = 2.48015872894767294178e-05;
const C4 = -2.75573143513906633035e-07;
const C5 = 2.08757232129817482790e-09;
const C6 = -1.13596475577881948265e-11;

/** sin on [-pi/4, pi/4], with y the tail of the reduced argument. */
function kSin(x, y) {
  const z = x * x;
  const w = z * z;
  const r = S2 + z * (S3 + z * S4) + z * w * (S5 + z * S6);
  const v = z * x;
  return x - ((z * (0.5 * y - v * r) - y) - v * S1);
}

/** cos on [-pi/4, pi/4], with y the tail of the reduced argument. */
function kCos(x, y) {
  const z = x * x;
  let w = z * z;
  const r = z * (C1 + z * (C2 + z * C3)) + w * w * (C4 + z * (C5 + z * C6));
  const hz = 0.5 * z;
  w = 1 - hz;
  return w + (((1 - w) - hz) + (z * r - x * y));
}

/** x as n * pi/2 + (a + b), |a + b| <= ~pi/4. */
function reduce(x) {
  const n = Math.round(x * INV_PIO2);
  const r = x - n * PIO2_1;
  const w = n * PIO2_1T;
  const a = r - w;
  return { n: ((n % 4) + 4) % 4, a, b: (r - a) - w };
}

export function sin(x) {
  if (!Number.isFinite(x)) return NaN;
  if (Math.abs(x) <= 0.7853981633974483) return kSin(x, 0);
  const { n, a, b } = reduce(x);
  return n === 0 ? kSin(a, b) : n === 1 ? kCos(a, b) : n === 2 ? -kSin(a, b) : -kCos(a, b);
}

export function cos(x) {
  if (!Number.isFinite(x)) return NaN;
  if (Math.abs(x) <= 0.7853981633974483) return kCos(x, 0);
  const { n, a, b } = reduce(x);
  return n === 0 ? kCos(a, b) : n === 1 ? -kSin(a, b) : n === 2 ? -kCos(a, b) : kSin(a, b);
}

const ATAN_HI = [4.63647609000806093515e-01, 7.85398163397448278999e-01,
  9.82793723247329054082e-01, 1.57079632679489655800e+00];
const ATAN_LO = [2.26987774529616870924e-17, 3.06161699786838301793e-17,
  1.39033110312309984516e-17, 6.12323399573676603587e-17];
const AT = [3.33333333333329318027e-01, -1.99999999998764832476e-01, 1.42857142725034663711e-01,
  -1.11111104054623557880e-01, 9.09088713343650656196e-02, -7.69187620504482999495e-02,
  6.66107313738753120669e-02, -5.83357013379057348645e-02, 4.97687799461593236017e-02,
  -3.65315727442169155270e-02, 1.62858201153657823623e-02];

export function atan(v) {
  if (Number.isNaN(v)) return NaN;
  const negative = v < 0;
  let x = Math.abs(v);
  if (x >= 2 ** 66) return negative ? -ATAN_HI[3] : ATAN_HI[3];
  let id = -1;
  if (x >= 0.4375) {
    if (x < 1.1875) {
      if (x < 0.6875) { id = 0; x = (2 * x - 1) / (2 + x); } else { id = 1; x = (x - 1) / (x + 1); }
    } else if (x < 2.4375) { id = 2; x = (x - 1.5) / (1 + 1.5 * x); } else { id = 3; x = -1 / x; }
  }
  const z = x * x;
  const w = z * z;
  const s1 = z * (AT[0] + w * (AT[2] + w * (AT[4] + w * (AT[6] + w * (AT[8] + w * AT[10])))));
  const s2 = w * (AT[1] + w * (AT[3] + w * (AT[5] + w * (AT[7] + w * AT[9]))));
  if (id < 0) return negative ? -(x - x * (s1 + s2)) : x - x * (s1 + s2);
  const r = ATAN_HI[id] - ((x * (s1 + s2) - ATAN_LO[id]) - x);
  return negative ? -r : r;
}

const PI = 3.1415926535897931160e+00;
const PI_LO = 1.2246467991473531772e-16;

export function atan2(y, x) {
  if (Number.isNaN(x) || Number.isNaN(y)) return NaN;
  if (y === 0) return x > 0 || Object.is(x, 0) ? y : (Object.is(y, -0) ? -PI : PI);
  if (x === 0) return y > 0 ? PI / 2 : -PI / 2;
  const z = atan(Math.abs(y / x));
  if (x > 0) return y > 0 ? z : -z;
  return y > 0 ? PI - (z - PI_LO) : (z - PI_LO) - PI;
}

/** acos through atan2, whose quotient sqrt((1 - x)(1 + x)) / x is exact-rounded. */
export function acos(x) {
  if (!(x >= -1 && x <= 1)) return NaN;
  return atan2(Math.sqrt((1 - x) * (1 + x)), x);
}

/** floor(log2(|x|)) for a normal x, read off its exponent bits: exact. */
export function exponentOf(x) {
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, x);
  return ((view.getUint16(0) >> 4) & 0x7ff) - 1023;
}
