// T-1246 measured 2026-09-20T18:27:46.533Z
// Darwin 25.6.0 arm64 / Apple M5 Max; Chromium 153.0.8010.12
// Headless Chromium; 390×780 touch and 1280×800; no CPU throttle; fresh context cold, repeat navigation warm.
// Published mirror: tools/measure_boot_phases.mjs --published --json.
// Receipt: tools/boot_phase_measurements.json. Seconds, not percentages.
export const BOOT_WEIGHTS = {
  "mobile": {
    "light": {
      "cold": {
        "scene": 0.2453,
        "terrain": 0.2309,
        "buildings": 0.1098,
        "ground": 0.2058,
        "flora": 1.7328,
        "people": 0.0841,
        "census": 0.0044,
        "interaction": 1.0129
      },
      "warm": {
        "scene": 0.2082,
        "terrain": 0.2212,
        "buildings": 0.102,
        "ground": 0.1547,
        "flora": 1.7652,
        "people": 0.0676,
        "census": 0.0226,
        "interaction": 0.8125
      }
    },
    "balanced": {
      "cold": {
        "scene": 0.1994,
        "terrain": 0.2317,
        "buildings": 0.0981,
        "ground": 0.2104,
        "flora": 2.2037,
        "people": 0.0805,
        "census": 0.0059,
        "interaction": 1.2458
      },
      "warm": {
        "scene": 0.2033,
        "terrain": 0.221,
        "buildings": 0.1023,
        "ground": 0.1632,
        "flora": 2.1791,
        "people": 0.0694,
        "census": 0.0028,
        "interaction": 0.8325
      }
    },
    "full": {
      "cold": {
        "scene": 0.2146,
        "terrain": 0.2323,
        "buildings": 0.0933,
        "ground": 0.2157,
        "flora": 2.7144,
        "people": 0.0807,
        "census": 0.0037,
        "interaction": 1.2213
      },
      "warm": {
        "scene": 0.2392,
        "terrain": 0.231,
        "buildings": 0.1023,
        "ground": 0.155,
        "flora": 2.847,
        "people": 0.0696,
        "census": 0.0236,
        "interaction": 0.8256
      }
    }
  },
  "desktop": {
    "light": {
      "cold": {
        "scene": 0.217,
        "terrain": 0.2352,
        "buildings": 0.1087,
        "ground": 0.2019,
        "flora": 1.7625,
        "people": 0.0789,
        "census": 0.0032,
        "interaction": 1.3141
      },
      "warm": {
        "scene": 0.2053,
        "terrain": 0.2324,
        "buildings": 0.1148,
        "ground": 0.1606,
        "flora": 1.7636,
        "people": 0.0702,
        "census": 0.0046,
        "interaction": 0.8743
      }
    },
    "balanced": {
      "cold": {
        "scene": 0.2138,
        "terrain": 0.2328,
        "buildings": 0.0924,
        "ground": 0.2156,
        "flora": 2.2373,
        "people": 0.0797,
        "census": 0.0034,
        "interaction": 1.2938
      },
      "warm": {
        "scene": 0.2034,
        "terrain": 0.2163,
        "buildings": 0.12,
        "ground": 0.1494,
        "flora": 2.1945,
        "people": 0.0723,
        "census": 0.0045,
        "interaction": 0.8738
      }
    },
    "full": {
      "cold": {
        "scene": 0.21,
        "terrain": 0.2325,
        "buildings": 0.0975,
        "ground": 0.2125,
        "flora": 2.7997,
        "people": 0.0831,
        "census": 0.0038,
        "interaction": 1.3217
      },
      "warm": {
        "scene": 0.1975,
        "terrain": 0.2328,
        "buildings": 0.1109,
        "ground": 0.1574,
        "flora": 2.8282,
        "people": 0.0699,
        "census": 0.0045,
        "interaction": 0.8875
      }
    }
  }
};
