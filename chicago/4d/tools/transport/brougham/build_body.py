# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the V19 body/finish specimen and exact native delivery contracts.

Fresh output only. Four actual producer invocations prove near/mid determinism;
no Blender, source pixels, terrain, browser or photographic acceptance is implied.
"""
from pathlib import Path
import argparse, collections, copy, hashlib, json, shutil, subprocess, sys, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, data):
    Path(p).write_text(json.dumps(data, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--validator-module', type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise ValueError('Fresh build directory required')
    a.output.mkdir(parents=True)
    sys.path.insert(0, str(HERE))
    from check_near import read, expanded, world_nodes, decoded_bounds, native_contacts
    from index_streams import write_indexed
    from body_geometry import check_preservation
    from static_master import static_master_contract
    baseline = json.loads((HERE / 'v18-protected-body-baseline.json').read_text())
    rows = []
    started = time.monotonic()
    for mode in ['near', 'mid']:
        generated = []
        for suffix in ['a', 'b']:
            out = a.output / (mode + '-' + suffix)
            command = [sys.executable, str(HERE / 'generate.py'), '--output', str(out), '--detail', mode,
                       '--lod-recipe', str(HERE / 'ring16-mid-lods.json'),
                       '--rear-quarter-recipe', str(HERE / 'rear-quarter.json')]
            result = subprocess.run(command, capture_output=True, text=True)
            (a.output / (mode + '-' + suffix + '.stdout')).write_text(result.stdout)
            (a.output / (mode + '-' + suffix + '.stderr')).write_text(result.stderr)
            if result.returncode:
                raise RuntimeError('Producer failed: ' + mode + '-' + suffix)
            generated.append(out / 'brougham.glb')
        assert generated[0].read_bytes() == generated[1].read_bytes(), 'Actual repeated generator differs'
        raw_name = 'brougham-source.glb' if mode == 'near' else 'brougham-mid-source.glb'
        indexed_name = 'brougham-' + mode + '.glb'
        raw = a.output / raw_name
        shutil.copyfile(generated[0], raw)
        indexing = write_indexed(raw, a.output / indexed_name)
        doc, binary = read(raw)
        protected = check_preservation(doc, binary, baseline['details'][mode])
        rows.append({'detail': mode, 'raw_file': raw_name, 'indexed_file': indexed_name,
                     'triangles': expanded(doc, binary)[1], 'parts': len(doc['extras']['parts']),
                     'meshes': len(doc['meshes']), 'nodes': len(doc['nodes']),
                     'materials': len(doc['materials']),
                     'bounds_m': decoded_bounds(doc, binary, world_nodes(doc)),
                     'protected': protected, **indexing})
    receipt = {'variant': 'V19_catalogue_body_and_finish', 'source_generated_twice_deterministic': True,
               'generation_invocations': 4, 'native_build_seconds': time.monotonic() - started,
               'rows': rows, 'photographic_accepted': False, 'world_budget_accepted': False,
               'prior_V18_lamp_protection': True}
    write(a.output / 'BUILD-RECEIPT.json', receipt)
    write(a.output / 'MID-BUILD-RECEIPT.json', {'variant': receipt['variant'], 'near': rows[0], 'mid': rows[1],
                                             'source_tessellation_only': True, 'photographic_accepted': False,
                                             'world_budget_accepted': False})
    reports = {}
    for row in rows:
        for kind, filename in [('raw', row['raw_file']), ('indexed', row['indexed_file'])]:
            name = 'V19-' + row['detail'] + '-' + kind + '.json'
            script = "const fs=require('fs'),v=require(process.argv[1]);v.validateBytes(new Uint8Array(fs.readFileSync(process.argv[2])),{uri:process.argv[2],maxIssues:10000}).then(r=>{process.stdout.write(JSON.stringify(r,null,2));if(r.issues.numErrors||r.issues.numWarnings)process.exitCode=1})"
            p = subprocess.run(['node', '-e', script, str(a.validator_module), str(a.output / filename)], capture_output=True)
            (a.output / name).write_bytes(p.stdout)
            (a.output / (name + '.stderr')).write_bytes(p.stderr)
            if p.returncode:
                raise RuntimeError('Actual glTF validation failed: ' + filename)
            reports[filename] = {'report': name, 'report_sha256': sha(a.output / name),
                                 'actual_input_sha256': sha(a.output / filename)}
    side = json.loads((HERE / 'archive-v18/brougham.json').read_text())
    side['previous_V18_visual_evidence'] = side['near_actual_visual_evidence']
    side['revision'] = 'v19_catalogue_body_and_finish_near_mid_study'
    side['native_variant'] = 'V19_catalogue_body_and_finish'
    side['previous_V18_source_history_note'] = side['source_history_note']
    side['source_history_note'] = 'Current V19 refines five body/pad occurrences and adds one driver piping occurrence.475near/309mid V18 unaffected geometry occurrences, accepted lamps/materials, contacts, frames and conservative proxy remain exact; hidden construction and optics reconstructed.'
    side['rendering'] = 'Original portable PBR factors; no image textures. Lossless near/mid indexing; eight merged material batches, including separate physical cabin glass. Material count is not render-pass or whole-world budget acceptance.'
    side['source_master_sha256'] = rows[0]['source_sha256']
    side['parameters_sha256'] = sha(HERE / 'parameters.json')
    side['near_actual_visual_evidence'] = 'Actual neutral native GLTFLoader studies exist for predecessor/C1 geometry. Current analytical-front-normal exact source visual review remains pending; no occupied/world/published-phone photographic acceptance.'
    side['status'] = 'V19 original source-bounded body/finish refinement; static empty reconstruction; photographic and production qualification pending'
    side['lod_appearance_accepted'] = {'near': False, 'mid': False}
    side['pending_deliverables'] = ['Final exact-source catalogue comparison and discrepancy review',
                                    'T3085 physical-interface, portable LOD and published phone/desktop qualification']
    for old, row in zip(side['lods'], rows):
        old.update(row)
        old['file'] = row['indexed_file']
        old['raw_mesh_batches'] = row['meshes']
        old['parked_material_groups'] = row['materials']
    doc, binary = read(a.output / rows[0]['raw_file'])
    side['static_master'] = static_master_contract(doc, binary, world_nodes(doc), rows[0]['source_sha256'])
    side['mid_provenance'].update(source_master_near_sha256=rows[0]['source_sha256'],
                                 build_receipt_sha256=sha(a.output / 'MID-BUILD-RECEIPT.json'),
                                 recipe='tools/transport/brougham/ring16-mid-lods.json',
                                 recipe_sha256=sha(HERE / 'ring16-mid-lods.json'),
                                 distance_lod_native_appearance_accepted=False,
                                 photographic_accepted=False, world_budget_accepted=False,
                                 current_near_triangles=rows[0]['triangles'], current_mid_triangles=rows[1]['triangles'])
    side['mid_provenance']['triangles'] = {row['detail']: row['triangles'] for row in rows}
    side['mid_provenance']['subdivision_records'] = {row['detail']: row['parts'] for row in rows}
    side['mid_provenance']['change'] = ('Current V19 source-tessellated near/mid body-and-finish specimen: '
        + str(rows[0]['triangles']) + '/' + str(rows[1]['triangles']) + ' triangles, '
        + str(rows[0]['parts']) + '/' + str(rows[1]['parts']) + ' subdivision records, eight materials and43nodes. '
        'All physical families,64spokes,16spring leaves,13runtime anchors and8static targets retained. '
        'Original conservative near proxy remains; photographic/world/published qualification pending.')
    side['mid_provenance']['appearance_history_note'] = 'V17 native appearance evidence and V18 lamp-only evidence are historical; neither supplies current V19 photographic or published LOD acceptance. Both original metadata files remain in their named archive directories.'
    write(a.output / 'brougham.json', side)
    source_names = ['LICENSE', 'generate.py', 'parameters.json', 'body_finish.py', 'body_geometry.py',
                    'build_body.py', 'index_streams.py', 'lods.json', 'ring16-mid-lods.json',
                    'quarter_surface.py', 'rear-quarter.json', 'source_details.py', 'static_master.py',
                    'lamp_geometry.py', 'v18-protected-body-baseline.json', 'analytical-normal-only-baseline.json']
    for row in rows:
        doc, binary = read(a.output / row['raw_file'])
        contract = {'scope': 'Exact V19 source body/finish delivery; photographic/world/phone acceptance pending',
                    **row, 'raw_sha256': row['source_sha256'],
                    'raw_bytes': row['source_bytes'], 'indexed_sha256': row['indexed_sha256'],
                    'expanded_PN_sha256': row['expanded_triangle_PN_sha256'],
                    'source_files': {name: sha(HERE / name) for name in source_names},
                    'delivery_metadata_files': {name: sha(a.output / name) for name in ['BUILD-RECEIPT.json', 'MID-BUILD-RECEIPT.json', 'brougham.json']},
                    'native_contacts': native_contacts(doc, binary),
                    'static_master': static_master_contract(doc, binary, world_nodes(doc), row['source_sha256']),
                    'reference_sha256': doc['extras']['source_reference']['sha256'],
                    'physical_category_triangle_counts': dict(sum((collections.Counter({p['name']: p['triangles']}) for p in doc['extras']['parts']), collections.Counter())),
                    'validator_reports': [reports[row['raw_file']], reports[row['indexed_file']]],
                    'native_variant': 'V19_catalogue_body_and_finish'}
        write(a.output / (row['detail'] + '-contract.json'), contract)
    print(json.dumps({'pass': True, 'output': str(a.output), 'rows': rows, 'actual_validator_reports': reports}, indent=2))


if __name__ == '__main__':
    main()
