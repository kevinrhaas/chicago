# 1919 Prairie, the Marshall Field Jr. house — reference copies for the image gate (T-3279)

Two Gatlin Institute advertisement plates of 1919 South Prairie Avenue, photographs of c. 1909-1912
showing the house as its 1902 enlargement left it (the Institute bought it in 1909). Both are public
domain (published in the United States in 1911-1912) and the copies are the image store's
(kevinrhaas/chicago-images, `prairie-1904/files/<id>.jpg`), unaltered.

| file | what |
|---|---|
| `cdn_almanac_1913_gatlin_plate.jpg` | Prairie library `a19-cdnalmanac-1913-gatlin-1919`: the Chicago Daily News Almanac for 1913, p. 619 (Internet Archive `chicagodailynews1913chic`), 1101 x 1600 px, sha256 `0d82a77e9db197b91d68e67cc3eb66520b9ec00b84890cd97447e0c5cd4c553f`; source record `data/sources/cdn_almanac_1913_gatlin_1919_plate.json` |
| `blue_book_1912_gatlin_plate.jpg` | Prairie library `a19-bluebook-1912-gatlin-1919`: the Chicago Blue Book for 1912, p. 28 (Internet Archive `chicagobluebooko1912chic`), 1045 x 1600 px, sha256 `c3491ed0b74e34bb08921b79398d06efd3aefb00ff685b3d8fe3c54a332623c5`; source record `data/sources/chicago_blue_book_1912_gatlin_1919_plate.json` |
| (camera) | `data/reference_views/marshall_field_jr_house_1919_prairie/cdn_almanac_1913.json`, solved from the 1913 plate and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How they are used.** `node tools/photo_match.mjs data/reference_views/marshall_field_jr_house_1919_prairie/cdn_almanac_1913.json`
renders the committed GLB from that camera beside the 1913 plate and writes the match record the image
gate reads. The 1912 plate is read to confirm it. The house's other pictures are T-3280's.
