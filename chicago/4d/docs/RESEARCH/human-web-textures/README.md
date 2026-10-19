# Bounded authored-human web textures

`tools/human_export.sh --master` keeps canonical Blender and exported source GLBs unchanged. Only its web derivative now follows: actual embedded-image alpha audit in a scratch GLB, pinned glTF Transform 4.5.0 Lanczos3 resize, native JPEG quality 92 for eligible opaque color images, then the existing Meshopt operation. LOD caps are 2048 / 1024 / 512 / 256 pixels. Images are never enlarged. There is no 4K claim or new image extension/decoder.

`human_web_texture_inputs.py` verifies decoded alpha extrema with Pillow; transparent images are excluded from JPEG. Images used by normal/roughness/other data slots are excluded, including an image shared by color and data slots. Alpha-preserving PNGs are still subject to the LOD dimension cap. Image names are labeled only in scratch data so the pinned CLI pattern can select eligible images. Canonical image/GLB bytes are untouched. The source alpha test found the actual selected 2048×2048 RGBA skin entirely opaque, extrema (255,255). A synthetic 4×4 RGBA texture containing one transparent pixel correctly takes the preserve branch without changing its source GLB.

The fixture and `--verify` branches retain their original Meshopt command byte-for-byte; no Blender was installed or run for this focused test. The authored path rejects unrecognized LOD filenames rather than selecting an arbitrary resolution. Pipeline command failures stop export; no contract assertions were weakened.

## Actual scratch receipt, 2026-10-18

The existing uncompressed `c4d_fixture.lod0.glb` was copied outside the repository and its embedded texture replaced with the actual selected 2K skin PNG. This synthetic combination tests delivery only; it is not a production human, UV-quality assertion or period outfit acceptance. Original combined input was about 4.58 MB. Every row below runs that same lod0 geometry, so the sizes deliberately do **not** claim final authored lower-LOD mesh costs.

| Texture cap | Actual JPEG dimensions | Meshopt GLB bytes | JPEG RGB RMSE vs resized PNG | PSNR |
|---|---|---:|---:|---:|
| 2048 | 2048×2048 | 640,276 | 1.955 | 42.31 dB |
| 1024 | 1024×1024 | 253,956 | 1.948 | 42.34 dB |
| 512 | 512×512 | 149,796 | 2.000 | 42.11 dB |
| 256 | 256×256 | 122,444 | 2.275 | 40.99 dB |

All exceed the focused 32 dB quality bound. JPEG quality was explicitly 92 in every command, not a default inferred from file size. Native JPEG reduces transfer bytes; its decoded GPU memory still follows pixel dimensions. Perceptual review on the actual model remains required.

Pinned CLI `resize --help` confirmed --width/--height are maximum bounds, preserve aspect and never increase dimensions. `jpeg --help` confirmed --formats, --quality, --pattern and --slots. Actual commands used `--formats '*' --quality 92 --pattern 'c4d_web_opaque_*' --slots '{baseColorTexture,emissiveTexture}'`.

Decoded NodeIO comparison found exact geometry equality between original and texture-processed GLB before Meshopt. After standard Meshopt, the 56-joint name set, idle/walk clips, morph target set and all five material slots remained unchanged. Joint TRS stayed within 1e-6 (observed normalization roundoff 1.2e-7); existing contract frame gates remain unchanged. Meshopt is the existing geometry transformation, rather than a lossless geometry-byte claim. Native JPEG MIME and actual decoded dimensions were checked. Detailed size/quality data is saved in `scratch-quality-receipts.json`; scratch CLI logs and structural comparison are under `/tmp/human-web-quality/` in this session.
