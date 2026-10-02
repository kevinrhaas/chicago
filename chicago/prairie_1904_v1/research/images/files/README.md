# Moved — the Prairie image files live in kevinrhaas/chicago-images

**This folder held the collection's first image store. Its files were deleted on 2026-10-02**, with
the owner's approval, after checking two things:
- Every one of its 295 files is in
  [kevinrhaas/chicago-images](https://github.com/kevinrhaas/chicago-images) (`prairie-1904/files/`).
  73 Robinson 1886 thumbnails there are newer re-derivations, and those are the ones the records
  cite.
- Nothing in the pre-fire, postfire or Prairie sites referenced the folder.

- The images are served at https://kevinrhaas.github.io/chicago-images/prairie-1904/files/.
- Records keep the logical path `research/images/files/<id>.jpg`, and the viewer maps it onto the
  image host (`research/images/STORE.json`, written by `tools/sync_image_store.py`).
- `tools/fetch_image.py` writes new images straight into the image store.
- `tools/validate.py` refuses any image file placed here.
