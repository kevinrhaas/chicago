# RETIRED — do not add files here

**The Prairie image collection moved to [kevinrhaas/chicago-images](https://github.com/kevinrhaas/chicago-images)
(`prairie-1904/files/`) on 2026-10-02**, on the owner's decision, so it can grow past what this
site's GitHub Pages limit allows. It is served at
https://kevinrhaas.github.io/chicago-images/prairie-1904/files/.

- `tools/fetch_image.py` writes there now, not here.
- Records keep the logical path `research/images/files/<id>.jpg`, and the viewer maps it onto the
  image host (`research/images/STORE.json`, written by `tools/sync_image_store.py`).
- The files below are the frozen first store, listed in `RETIRED.json`. They are still published
  as the viewer's fallback while the image host is new. `tools/validate.py` refuses any file that is
  not on that list.
- Once the image host is confirmed serving, this folder can be dropped from `tools/publish.py`
  and deleted.
