// T-2164 measured 2026-10-08T06:15:17.726Z by tools/measure_boot_bytes.mjs
// Wire (gzip) bytes each essential boot phase downloads on a first visit, from the app's own
// Resource Timing meter, fresh context, published mirror. Bytes, not seconds: the
// arrival forecast divides them by the link it measures (boot-forecast.js).
export const BOOT_BYTES = {
  "mobile": {
    "light": {
      "scene": 5864042,
      "terrain": 1798519,
      "buildings": 2170275,
      "ground": 1530268,
      "flora": 153859,
      "interaction": 1276595
    },
    "balanced": {
      "scene": 5864042,
      "terrain": 1798519,
      "buildings": 2170275,
      "ground": 1530268,
      "flora": 153859,
      "interaction": 1276595
    },
    "full": {
      "scene": 5864042,
      "terrain": 1798519,
      "buildings": 2170275,
      "ground": 1530268,
      "flora": 153859,
      "interaction": 1276595
    }
  },
  "desktop": {
    "light": {
      "scene": 5864042,
      "terrain": 1798519,
      "buildings": 2170275,
      "ground": 1436918,
      "flora": 153859,
      "interaction": 1276595
    },
    "balanced": {
      "scene": 5864042,
      "terrain": 1798519,
      "buildings": 2170275,
      "ground": 1436918,
      "flora": 153859,
      "interaction": 1276595
    },
    "full": {
      "scene": 5864042,
      "terrain": 1798519,
      "buildings": 2170275,
      "ground": 1436918,
      "flora": 153859,
      "interaction": 1276595
    }
  }
};
