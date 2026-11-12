#!/usr/bin/env python3
"""T-3532: reproducible, offline audio deliveries. Requires ffmpeg/ffprobe.

Originals never enter the web payload. Music Opus packets are remuxed losslessly;
AAC is an alternative for clients that cannot play Ogg/Opus, never a second fetch
on the happy path. Effects are explicitly derived from Freesound HQ MP3 previews,
not mislabelled as lossless masters. Run from any directory.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / 'assets/audio/originals'
OUT = ROOT / 'renderers/web/audio'


def run(*args):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *map(str, args)], check=True)


def fingerprint(path):
    return {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def encode_pinned_river(loop, mp3):
    # Never replace the owner-accepted bytes until the new encoding is identical.
    with tempfile.NamedTemporaryFile(dir=mp3.parent, prefix='.river-', suffix='.mp3', delete=False) as tmp:
        candidate = Path(tmp.name)
    try:
        subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-threads', '1',
            '-filter_threads', '1', '-f', 'f32le', '-ar', '48000', '-ac', '1', '-i', 'pipe:0',
            '-c:a', 'libmp3lame', '-b:a', '128k', '-y', str(candidate)], input=loop.astype('<f4').tobytes(), check=True)
        if fingerprint(candidate) != {'bytes': 352940, 'sha256': '6831b7ad102ec023194c4040776c5245b6cb47451d652a94a07dc742e28362af'}:
            raise ValueError('river: delivery differs from the owner-accepted loop; accepted destination unchanged')
        candidate.replace(mp3)  # Atomic same-filesystem rename after verification.
    finally:
        candidate.unlink(missing_ok=True)


RAGTIME = ORIGINALS / '1904-ragtime'
RAGTIME_LUFS = -17.5     # one listening level across the shuffled set (sources span -15.0..-17.9)
RAGTIME_TAIL_S = .4      # trailing silence kept before the next shuffled track
RAGTIME_OPUS = '64k'     # stereo Opus VBR; one streamed cue at a time, never decoded whole
RAGTIME_AAC = '112k'     # AAC-LC fallback for browsers without Ogg/Opus (older iPhone Safari)


def integrated_lufs(path):
    log = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', str(path), '-map', '0:a', '-af', 'ebur128',
        '-f', 'null', '-'], capture_output=True, text=True, check=True).stderr
    summary = log[log.rindex('Summary:'):]
    return float(summary.split('I:', 1)[1].split('LUFS', 1)[0])


def ragtime_1904(encode=True):
    """T-3569: the owner's ten ragtime MP3s are the whole 1904 playlist, played shuffled.

    Each is decoded once, given one static gain to a shared integrated loudness (no
    compression or limiting), trimmed of trailing silence beyond RAGTIME_TAIL_S, and
    encoded to a small Opus stream with an AAC fallback. Cover art and tags are dropped.
    """
    sr, out = 48000, []
    folder = OUT / '1904'
    folder.mkdir(parents=True, exist_ok=True)
    for file in sorted(RAGTIME.glob('*.mp3')):
        key = 'ragtime-' + file.stem.lower()
        title = file.stem.replace('-', ' ')
        opus, aac = folder / (key + '.ogg'), folder / (key + '.m4a')
        source_lufs = integrated_lufs(file)
        gain_db = round(RAGTIME_LUFS - source_lufs, 2)
        raw = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(file), '-map', '0:a',
            '-ac', '2', '-ar', str(sr), '-f', 'f32le', '-'])
        pcm = np.frombuffer(raw, dtype='<f4').reshape(-1, 2) * np.float32(10 ** (gain_db / 20))
        loud = np.flatnonzero(np.max(np.abs(pcm), axis=1) > 10 ** (-50 / 20))
        end = min(len(pcm), int(loud[-1]) + 1 + int(RAGTIME_TAIL_S * sr))
        pcm = pcm[:end].copy()
        fade = int(.25 * sr)
        pcm[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
        peak = float(np.max(np.abs(pcm)))
        if peak > .99: raise ValueError(f'{file.name}: loudness match would clip ({peak:.3f})')
        if encode:
            pipe = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-threads', '1', '-f', 'f32le', '-ar', str(sr), '-ac', '2',
                '-i', '-', '-map_metadata', '-1', '-metadata', f'title={title}']
            subprocess.run([*pipe, '-c:a', 'libopus', '-b:a', RAGTIME_OPUS, '-vbr', 'on', '-application', 'audio',
                str(opus)], input=pcm.tobytes(), check=True)
            subprocess.run([*pipe, '-c:a', 'aac', '-b:a', RAGTIME_AAC, '-movflags', '+faststart',
                str(aac)], input=pcm.tobytes(), check=True)
        out.append({'id': key, 'kind': 'music', 'era': '1904', 'title': title,
            'duration_s': round(len(pcm) / sr, 3), 'original': str(file.relative_to(ROOT)),
            'original_integrity': fingerprint(file),
            'provenance': 'Owner-supplied MP3 (artist tag Kevin R Haas; album tag "Made with Mozart"). Period-style ragtime written for the app, not an archival performance or recording.',
            'rights': 'Owner authorized use and distribution in the app, 2026-11-12; no open asset licence asserted.',
            'processing': f'MP3 decoded to 48 kHz stereo; static gain {gain_db:+.2f} dB from {source_lufs:.1f} to {RAGTIME_LUFS} LUFS integrated; trailing silence trimmed to {RAGTIME_TAIL_S} s with 250 ms fade; Opus {RAGTIME_OPUS} VBR, AAC-LC {RAGTIME_AAC} fallback. No compression, limiting or EQ.',
            'opus': str(opus.relative_to(OUT)), 'aac': str(aac.relative_to(OUT)),
            'delivery': {'opus': fingerprint(opus), 'aac': fingerprint(aac)}})
    if len(out) != 10: raise ValueError(f'1904 ragtime: expected the owner\'s ten tracks, found {len(out)}')
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assets = []
    for file in sorted(ORIGINALS.glob('*.m4a')):
        era = '1904' if 'Waltz' in file.name else '1812' if 'Frontier' in file.name else '1835'
        key = file.stem.lower()
        folder = OUT / era
        folder.mkdir(exist_ok=True)
        opus, aac = folder / (key + '.ogg'), folder / (key + '.m4a')
        if '--effects-only' not in sys.argv and '--library-only' not in sys.argv:
            run('-i', file, '-c:a', 'copy', opus)
            run('-i', file, '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', aac)
        info = json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-show_format', '-of', 'json', str(file)]))['format']
        assets.append({'id': key, 'kind': 'music', 'era': era,
            'title': file.stem.split('-', 1)[1].replace('-', ' '),
            'duration_s': float(info['duration']), 'original': str(file.relative_to(ROOT)),
            'original_integrity': fingerprint(file),
            'provenance': 'Owner-supplied; file metadata identifies Suno-generated music. Not an archival performance.',
            'rights': 'Owner authorized use and distribution in the app, 2026-11-10; no open asset licence asserted.',
            'opus': str(opus.relative_to(OUT)), 'aac': str(aac.relative_to(OUT)),
            'delivery': {'opus': fingerprint(opus), 'aac': fingerprint(aac)}})
        if era == '1904':
            # T-3569: the owner replaced the 1904 waltzes with his ragtime set.
            assets[-1].update(runtime_enabled=False,
                review_note='Retired from 1904 playback by the owner, 2026-11-12, for the ten-track ragtime playlist. Original and verified deliveries retained.')
    assets += ragtime_1904('--effects-only' not in sys.argv and '--library-only' not in sys.argv)
    for key, name, creator, source, start in [
        ('wind', '475448_7009965-hq.mp3', 'o_ciz', 'https://freesound.org/people/o_ciz/sounds/475448/', 15),
        ('river-held', '577323_97550-hq.mp3', 'TRP', 'https://freesound.org/people/TRP/sounds/577323/', 10),
        ('river', '575244_97550-hq.mp3', 'TRP', 'https://freesound.org/people/TRP/sounds/575244/', 121),
        ('lake', '442543_5902878-hq.mp3', 'BonnyOrbit', 'https://freesound.org/people/BonnyOrbit/sounds/442543/', 20),
    ]:
        file = ORIGINALS / name
        if key == 'river' and fingerprint(file) != {'bytes': 4995639, 'sha256': '8ab476464f7d1280514f6a405988550f423b572e9fe3900b29b776cfba77ab48'}:
            raise ValueError('river: source preview differs from the approved source; destination unchanged')
        # Sample-exact seam: middle 2..22, then end 22..24 crossfaded to start 0..2.
        # Working in PCM avoids filter-graph time-base/EOF ambiguity.
        if key == 'river':
            # Preserve the owner's accepted sample-index crop; input seeking can
            # change resampling alignment. Hash-pinned below to the heard MP3.
            raw = subprocess.check_output(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
                '-threads', '1', '-filter_threads', '1', '-i', str(file), '-ac', '1', '-ar', '48000',
                '-f', 'f32le', 'pipe:1'])
            pcm = np.frombuffer(raw, dtype='<f4')[121*48000:145*48000].copy()
        else:
            raw = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(start), '-i', str(file),
                '-t', '24', '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'])
            pcm = np.frombuffer(raw, dtype='<f4')
        sr = 48000
        if len(pcm) < 24 * sr:
            raise ValueError(f'{file.name}: incomplete 24-second source excerpt')
        fade = np.linspace(0, 1, 2 * sr, dtype=np.float32)
        seam = pcm[22*sr:24*sr] * (1-fade) + pcm[:2*sr] * fade
        loop = np.concatenate([pcm[2*sr:22*sr], seam])
        if key == 'wind': loop *= 10
        if np.max(np.abs(loop)) > .99: raise ValueError(f'{key}: processing would clip')
        mp3 = OUT / (key + '.mp3')
        if key == 'river':
            encode_pinned_river(loop, mp3)
        else:
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '1',
                '-i', '-', '-c:a', 'libmp3lame', '-b:a', '128k', str(mp3)], input=loop.astype('<f4').tobytes(), check=True)
        assets.append({'id': key, 'kind': 'environment', 'title': 'Wind through leaves' if key == 'wind' else 'Light water on rocks' if key == 'river' else 'Previous river recording (held)' if key == 'river-held' else 'Lake Maggiore shore waves',
            'creator': creator, 'source_url': source, 'license': 'CC0-1.0',
            'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'acquired': '2026-11-11' if key == 'river' else '2026-11-10', 'original': str(file.relative_to(ROOT)), 'original_integrity': fingerprint(file),
            'provenance': 'Real-world recording per creator; HQ MP3 preview, not the lossless original. Chicago placement is reconstructed.',
            'processing': f'24-second excerpt from {start}s; mono; 2-second crossfade seam; wind gain +20 dB only; 48 kHz MP3 128 kbps.',
            'duration_s': 22, 'url': mp3.name, 'delivery': fingerprint(mp3)})
        if key == 'river':
            assets[-1].update(runtime_enabled=True,
                provenance='Real lake-water field recording on rocks at Manitoulin, summer 2008, per creator; Freesound HQ MP3 preview, not the original download. Used as a reconstructed acoustic proxy for the nearly still Chicago River; rocky lake substrate is not evidence of the historical river bank.',
                processing='Full preview decoded to mono 48 kHz before sample-index crop 121–145 s; 2-second linear end-to-start overlap; 22-second loop; unity gain; MP3 128 kbps. No EQ, normalization, denoising, gating, stretching or synthesis.',
                review_note='Owner selected "Light water on rocks" from the three audition samples, 2026-11-11 (TRP575244). Exact accepted loop bytes retained. Lake waves, slough treatment and insects remain separate and unchanged.')
        if key == 'river-held':
            assets[-1].update(runtime_enabled=False,
                review_note='Held from scene playback after owner listening review, 2026-11-11: too much moving/babbling water for the nearly still river. Retained for audition; replaced in the scene by the owner-selected calmer water recording. Lake waves and slough classification remain separate.')
    # Reviewable library additions stay opt-in to scene authoring. The runtime
    # only requests explicitly scheduled IDs; catalogue membership is not a cue.
    intake = ROOT / 'assets/audio/intake.json'
    if intake.exists():
        folder = OUT / 'candidates'
        folder.mkdir(exist_ok=True)
        for candidate in json.loads(intake.read_text())['assets']:
            file = ROOT / candidate['original']
            proof = json.loads((ROOT / candidate['evidence']).read_text())
            if fingerprint(file)['sha256'] != proof['file_sha256']:
                raise ValueError(f'{file}: acquired source hash changed')
            raw = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(candidate['excerpt_start_s']),
                '-i', str(file), '-t', str(candidate['excerpt_duration_s']), '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'])
            pcm = np.frombuffer(raw, dtype='<f4').copy()
            loop = candidate['category'] == 'insects' and len(pcm) >= 24 * 48000
            if loop:
                fade = np.linspace(0, 1, 96000, dtype=np.float32)
                pcm = np.concatenate([pcm[96000:22*48000], pcm[22*48000:24*48000]*(1-fade)+pcm[:96000]*fade])
            else:
                edge = min(480, len(pcm)//2)
                pcm[:edge] *= np.linspace(0, 1, edge)
                pcm[-edge:] *= np.linspace(1, 0, edge)
            peak = float(np.max(np.abs(pcm)))
            gain = min(1, .85 / max(peak, .000001))
            pcm *= gain
            delivery = folder / (candidate['id'] + '.mp3')
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '1',
                '-i', '-', '-c:a', 'libmp3lame', '-b:a', '128k', str(delivery)], input=pcm.astype('<f4').tobytes(), check=True)
            assets.append({**candidate, 'original_integrity': fingerprint(file),
                'duration_s': len(pcm)/48000, 'url': str(delivery.relative_to(OUT)), 'delivery': fingerprint(delivery),
                'loop': loop, 'gain_applied': gain,
                'processing': 'Mono 48 kHz MP3 128 kbps; '+('2-second crossfade seam.' if loop else '10 ms edge fades; excerpt requires event editing.'),
                'provenance': candidate['source_format']+'. '+candidate['placement_note']})
    # Ship a small engine-neutral classification sidecar derived from the existing
    # epoch vectors. Unknown wetlands are quiet, never silently classified as river.
    datum = json.loads((ROOT / 'data/datum.json').read_text())
    zones = {}
    for year in ['1812', '1835', '1904']:
        scene = json.loads((ROOT / f'data/scenes/{year}.json').read_text())
        epoch = scene['terrain_epoch']; rows = []
        for name in ['river', 'branches', 'shoreline', 'hydrology']:
            path = ROOT / f'data/terrain/epochs/{epoch}/{name}.geojson'
            if not path.exists(): continue
            for feature in json.loads(path.read_text())['features']:
                g, props = feature['geometry'], feature['properties']
                if g['type'] == 'Polygon' and props.get('kind') == 'water':
                    rows.append({'id': feature.get('id'), 'kind': 'river', 'polygon': [
                        [[round(e-datum['origin_utm_e'],2), round(n-datum['origin_utm_n'],2)] for e,n,*_ in ring]
                        for ring in g['coordinates']], 'source_path': str(path.relative_to(ROOT))})
                elif name == 'hydrology' and g['type'] == 'LineString':
                    rows.append({'id': feature.get('id'), 'kind': 'slough', 'width_m': props.get('drafted_width_m', 8),
                        'line': [[round(e-datum['origin_utm_e'],2),round(n-datum['origin_utm_n'],2)] for e,n,*_ in g['coordinates']],
                        'source_path': str(path.relative_to(ROOT))})
        zones[year] = {'epoch': epoch, 'features': rows}
    catalog = {'version': 1, 'music_eras_separate': True, 'music_shuffle_eras': ['1904'], 'water_zones': zones, 'assets': assets}
    (OUT / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    (ROOT / 'assets/audio/catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    print(f'Audio: {len(assets)} catalogued assets; alternatives are fetched only when needed.')


def ragtime_only():
    """T-3569: rebuild only the 1904 playlist inside the committed catalogue.

    Every other delivery is hash-pinned to verified R2 objects and stays byte-for-byte;
    a full regeneration on a different ffmpeg build would re-encode them."""
    paths = [OUT / 'catalog.json', ROOT / 'assets/audio/catalog.json']
    catalog = json.loads(paths[0].read_text())
    rows = [a for a in catalog['assets'] if not a['id'].startswith('ragtime-')]
    for a in rows:
        if a['kind'] == 'music' and a['era'] == '1904':
            a.update(runtime_enabled=False,
                review_note='Retired from 1904 playback by the owner, 2026-11-12, for the ten-track ragtime playlist. Original and verified deliveries retained.')
    at = max(i for i, a in enumerate(rows) if a['kind'] == 'music') + 1
    catalog['assets'] = rows[:at] + ragtime_1904() + rows[at:]
    catalog = {'version': catalog['version'], 'music_eras_separate': True, 'music_shuffle_eras': ['1904'],
        **{k: v for k, v in catalog.items() if k not in ('version', 'music_eras_separate', 'music_shuffle_eras')}}
    for path in paths: path.write_text(json.dumps(catalog, indent=2) + '\n')
    print('Audio: 1904 ragtime playlist rebuilt; other deliveries untouched.')


if __name__ == '__main__':
    ragtime_only() if '--ragtime-only' in sys.argv else main()
