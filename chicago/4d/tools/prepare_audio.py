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
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / 'assets/audio/originals'
OUT = ROOT / 'renderers/web/audio'


def run(*args):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *map(str, args)], check=True)


def fingerprint(path):
    return {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


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
    for key, name, creator, source, start in [
        ('wind', '475448_7009965-hq.mp3', 'o_ciz', 'https://freesound.org/people/o_ciz/sounds/475448/', 15),
        ('river', '577323_97550-hq.mp3', 'TRP', 'https://freesound.org/people/TRP/sounds/577323/', 10),
        ('lake', '442543_5902878-hq.mp3', 'BonnyOrbit', 'https://freesound.org/people/BonnyOrbit/sounds/442543/', 20),
    ]:
        file = ORIGINALS / name
        # Sample-exact seam: middle 2..22, then end 22..24 crossfaded to start 0..2.
        # Working in PCM avoids filter-graph time-base/EOF ambiguity.
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
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '1',
            '-i', '-', '-c:a', 'libmp3lame', '-b:a', '128k', str(mp3)], input=loop.astype('<f4').tobytes(), check=True)
        assets.append({'id': key, 'kind': 'environment', 'title': 'Wind through leaves' if key == 'wind' else 'Gentle riverbank lapping' if key == 'river' else 'Lake Maggiore shore waves',
            'creator': creator, 'source_url': source, 'license': 'CC0-1.0',
            'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'acquired': '2026-11-10', 'original': str(file.relative_to(ROOT)), 'original_integrity': fingerprint(file),
            'provenance': 'Real-world recording per creator; HQ MP3 preview, not the lossless original. Chicago placement is reconstructed.',
            'processing': f'24-second excerpt from {start}s; mono; 2-second crossfade seam; wind gain +20 dB only; 48 kHz MP3 128 kbps.',
            'duration_s': 22, 'url': mp3.name, 'delivery': fingerprint(mp3)})
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
    catalog = {'version': 1, 'music_eras_separate': True, 'water_zones': zones, 'assets': assets}
    (OUT / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    (ROOT / 'assets/audio/catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    print(f'Audio: {len(assets)} catalogued assets; alternatives are fetched only when needed.')


if __name__ == '__main__':
    main()
