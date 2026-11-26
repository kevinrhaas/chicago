// T-2164 measured 2026-11-26T04:38:04.831Z by tools/measure_boot_bytes.mjs
// Wire (gzip) bytes each essential boot phase downloads on a first visit, from the app's own
// Resource Timing meter, fresh context, https://dev.chicago.polecat.live/4d/dev/. Bytes, not seconds: the
// arrival forecast divides them by the link it measures (boot-forecast.js). Keyed
// year › device › detail: each year is a different town (T-3758).
export const BOOT_BYTES = {
  "1812": {
    "mobile": {
      "light": {
        "scene": 2650443,
        "terrain": 2135860,
        "buildings": 7253412,
        "ground": 3412132,
        "flora": 1519407,
        "interaction": 1700104
      },
      "balanced": {
        "scene": 2650443,
        "terrain": 2113852,
        "buildings": 7275420,
        "ground": 3412132,
        "flora": 2105147,
        "interaction": 1700104
      },
      "full": {
        "scene": 2650443,
        "terrain": 2113852,
        "buildings": 7275420,
        "ground": 3412132,
        "flora": 2105147,
        "interaction": 1700104
      }
    },
    "desktop": {
      "light": {
        "scene": 2650443,
        "terrain": 2135860,
        "buildings": 7253412,
        "ground": 3412132,
        "flora": 1519407,
        "interaction": 1700104
      },
      "balanced": {
        "scene": 2650443,
        "terrain": 2113852,
        "buildings": 7275420,
        "ground": 3412132,
        "flora": 2105147,
        "interaction": 1700104
      },
      "full": {
        "scene": 2650443,
        "terrain": 2113852,
        "buildings": 7275420,
        "ground": 3412132,
        "flora": 2105147,
        "interaction": 1700104
      }
    }
  },
  "1835": {
    "mobile": {
      "light": {
        "scene": 5909763,
        "terrain": 2150621,
        "buildings": 3342724,
        "ground": 1498656,
        "flora": 1563253,
        "interaction": 2861411
      },
      "balanced": {
        "scene": 5909763,
        "terrain": 2150621,
        "buildings": 3342724,
        "ground": 1498656,
        "flora": 2148993,
        "interaction": 2861411
      },
      "full": {
        "scene": 5909763,
        "terrain": 2150621,
        "buildings": 3342724,
        "ground": 1498656,
        "flora": 2148993,
        "interaction": 2861411
      }
    },
    "desktop": {
      "light": {
        "scene": 5909763,
        "terrain": 2172629,
        "buildings": 3320716,
        "ground": 4243987,
        "flora": 1563253,
        "interaction": 2861411
      },
      "balanced": {
        "scene": 5909763,
        "terrain": 2150621,
        "buildings": 3320716,
        "ground": 4243987,
        "flora": 2171001,
        "interaction": 2861411
      },
      "full": {
        "scene": 5909763,
        "terrain": 2172629,
        "buildings": 3320716,
        "ground": 4243987,
        "flora": 2148993,
        "interaction": 2861411
      }
    }
  },
  "1871": {
    "mobile": {
      "light": {
        "scene": 4884044,
        "terrain": 785280,
        "buildings": 2349718,
        "ground": 8369839,
        "flora": 0,
        "interaction": 1449157
      },
      "balanced": {
        "scene": 4884044,
        "terrain": 763272,
        "buildings": 2371726,
        "ground": 8369839,
        "flora": 0,
        "interaction": 1449157
      },
      "full": {
        "scene": 4884044,
        "terrain": 763272,
        "buildings": 2371726,
        "ground": 8369839,
        "flora": 0,
        "interaction": 1449157
      }
    },
    "desktop": {
      "light": {
        "scene": 4884044,
        "terrain": 785280,
        "buildings": 2349718,
        "ground": 8369839,
        "flora": 0,
        "interaction": 1449157
      },
      "balanced": {
        "scene": 4884044,
        "terrain": 763272,
        "buildings": 2349718,
        "ground": 8977587,
        "flora": 0,
        "interaction": 1449157
      },
      "full": {
        "scene": 4906240,
        "terrain": 785280,
        "buildings": 2349718,
        "ground": 8955579,
        "flora": 0,
        "interaction": 1449157
      }
    }
  },
  "1904": {
    "mobile": {
      "light": {
        "scene": 65003879,
        "terrain": 2151349,
        "buildings": 2459764,
        "ground": 8626097,
        "flora": 3888,
        "interaction": 4148200
      },
      "balanced": {
        "scene": 42236851,
        "terrain": 2151349,
        "buildings": 2437756,
        "ground": 8646984,
        "flora": 1121,
        "interaction": 4152088
      },
      "full": {
        "scene": 63938300,
        "terrain": 2173357,
        "buildings": 2437756,
        "ground": 8624976,
        "flora": 5009,
        "interaction": 4148200
      }
    },
    "desktop": {
      "light": {
        "scene": 42236851,
        "terrain": 2173357,
        "buildings": 2437756,
        "ground": 12309421,
        "flora": 3957,
        "interaction": 1353839
      },
      "balanced": {
        "scene": 65731882,
        "terrain": 2151349,
        "buildings": 2459764,
        "ground": 10100869,
        "flora": 0,
        "interaction": 4152088
      },
      "full": {
        "scene": 64146811,
        "terrain": 2173357,
        "buildings": 2437756,
        "ground": 10100869,
        "flora": 3888,
        "interaction": 4148200
      }
    }
  }
};
