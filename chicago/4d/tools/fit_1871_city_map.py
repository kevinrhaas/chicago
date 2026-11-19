#!/usr/bin/env python3
"""Recompute the Mitchell 1870 map fit from the retained manual control picks.

Run from any directory:
    python3 tools/fit_1871_city_map.py --check

The input is data/context/1871/plan.json. The affine calculation uses the Python
standard library; --check also uses pyproj to independently derive target
coordinates. It never modifies the existing 1849 registration or map geometry.
The fitted numbers describe map registration, not surveyed building accuracy.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/context/1871/plan.json"


def solve(matrix, vector):
    """Solve this small normal system with partial-pivot elimination."""
    rows = [list(row) + [value] for row, value in zip(matrix, vector)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(rows[row][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        if abs(divisor) < 1e-12:
            raise ValueError("Control points do not support an affine fit")
        rows[column] = [value / divisor for value in rows[column]]
        for other in range(3):
            if other == column:
                continue
            factor = rows[other][column]
            rows[other] = [a - factor * b for a, b in zip(rows[other], rows[column])]
    return [row[3] for row in rows]


def fit(controls):
    rows = [[*point["pixel"], 1] for point in controls]
    normal = [[sum(row[i] * row[j] for row in rows) for j in range(3)] for i in range(3)]
    axes = []
    for axis in range(2):
        rhs = [sum(row[i] * point["local"][axis] for row, point in zip(rows, controls)) for i in range(3)]
        axes.append(solve(normal, rhs))
    east, north = axes
    residuals = []
    for row, point in zip(rows, controls):
        predicted = [sum(a * b for a, b in zip(row, axis)) for axis in axes]
        residuals.append(math.dist(predicted, point["local"]))
    return {
        "coefficients": dict(zip("abcdef", east + north)),
        "rms_m": math.sqrt(sum(value * value for value in residuals) / len(residuals)),
        "max_residual_m": max(residuals),
        "residuals_m": dict(zip((point["id"] for point in controls), residuals)),
    }


def project(point, coefficients):
    x, y = point
    return [coefficients['a'] * x + coefficients['b'] * y + coefficients['c'],
            coefficients['d'] * x + coefficients['e'] * y + coefficients['f']]


def verify_modern_targets():
    """Recompute portable OSM targets and verify actual named-road connectivity."""
    from pyproj import Transformer
    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:26916', always_xy=True)
    origin = [447072.7, 4637395.8]
    modern = json.loads((ROOT / 'data/traces/gcp/mitchell_1870_modern_targets.json').read_text())
    primitives_path = ROOT / modern['portable_primitive_extract']
    primitive = json.loads(primitives_path.read_text())
    nodes = {node['id']: node for node in primitive['nodes']}
    ways = {way['id']: way for way in primitive['ways']}
    maximum = 0.0
    for target in modern['targets']:
        projected = []
        families = target['osm_way_ids']
        for node_id in target['osm_node_ids']:
            node = nodes[node_id]
            e, n = transformer.transform(node['lon'], node['lat'])
            projected.append([e - origin[0], n - origin[1]])
            for family, way_ids in families.items():
                adjacent = set()
                for way_id in way_ids:
                    way = ways[way_id]
                    if not way['tags'].get('highway'):
                        raise ValueError(f'Control way lacks roadway type: {way_id}')
                    refs = way['nodes']
                    if not all(ref in nodes for ref in refs):
                        raise ValueError(f'Portable way has missing node references: {way_id}')
                    for index, ref in enumerate(refs):
                        if ref != node_id:
                            continue
                        if index:
                            adjacent.add(refs[index - 1])
                        if index + 1 < len(refs):
                            adjacent.add(refs[index + 1])
                if len(adjacent) < 2:
                    raise ValueError(f"Named road does not continue through target: {target['id']} {family}")
        mean = [sum(point[axis] for point in projected) / len(projected) for axis in range(2)]
        error = math.dist(mean, [target['local_e'], target['local_n']])
        maximum = max(maximum, error)
        if error > 0.008:
            raise ValueError(f"Portable target projection changed: {target['id']} ({error} m)")
    original = json.loads((ROOT / 'data/traces/gcp/rees_rucker_1849_gcps.json').read_text())
    for gcp in original['gcps']:
        target = gcp['modern']
        e, n = transformer.transform(target['lon'], target['lat'])
        error = math.dist([e - origin[0], n - origin[1]], [target['local_e'], target['local_n']])
        maximum = max(maximum, error)
        if error > 0.008:
            raise ValueError('Original target CRS convention changed: ' + gcp['map_feature'])
    return {'portable_targets': len(modern['targets']), 'portable_nodes': len(nodes),
            'portable_ways': len(ways), 'max_rounding_error_m': maximum,
            'portable_extract_sha256': hashlib.sha256(primitives_path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify fit, reserved checks, targets and projected geometry')
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text())
    control = plan['map_control']
    fit_controls = [point for point in control['controls'] if point.get('role', 'fit') == 'fit']
    checks = [point for point in control['controls'] if point.get('role') == 'check']
    result = fit(fit_controls)
    check_errors = [math.dist(project(point['pixel'], result['coefficients']), point['local']) for point in checks]
    if checks:
        result['held_out_rms_m'] = math.sqrt(sum(value * value for value in check_errors) / len(check_errors))
        result['held_out_max_m'] = max(check_errors)
    if not args.check:
        print(json.dumps(result, indent=2))
        return
    target_check = verify_modern_targets()
    raster = ROOT / control['raster']
    if hashlib.sha256(raster.read_bytes()).hexdigest() != control['sha256']:
        raise ValueError('The map raster differs from the reviewed original')
    controls_path = ROOT / control['control_file']
    if hashlib.sha256(controls_path.read_bytes()).hexdigest() != control['controls_sha256']:
        raise ValueError('The reviewed raw control annotations changed')
    annotation = json.loads(controls_path.read_text())
    if annotation['controls'] != control['controls']:
        raise ValueError('Plan controls differ from raw annotations')
    original = json.loads((ROOT / 'data/traces/gcp/rees_rucker_1849_gcps.json').read_text())
    targets = {point['map_feature']: point['modern'] for point in original['gcps']}
    modern = json.loads((ROOT / 'data/traces/gcp/mitchell_1870_modern_targets.json').read_text())
    extra = {point['id']: point for point in modern['targets']}
    for point in control['controls']:
        target = extra[point['modern_target_id']] if point.get('modern_target_id') else targets[point['feature']]
        if point['local'] != [target['local_e'], target['local_n']]:
            raise ValueError(f"Modern control target changed: {point['id']}")
    for key, value in result['coefficients'].items():
        if abs(value - control['coefficients'][key]) > 1e-6:
            raise ValueError(f'Stored fit differs: {key}')
    for key in ('rms_m', 'max_residual_m', 'held_out_rms_m', 'held_out_max_m'):
        if abs(result[key] - control[key]) > 0.001:
            raise ValueError(f'Stored fit statistic differs: {key}')
    check_ids = {point['id'] for point in checks}
    count = 0
    for section in ('rivers', 'streets', 'railways', 'parks', 'bridges', 'water_polygons', 'exclusions'):
        for feature in plan[section]:
            if check_ids.intersection(feature.get('reading_control_ids', [])):
                raise ValueError('Reserved check used to anchor geometry: ' + feature['id'])
            raw = feature.get('source_pixels')
            if not raw or feature.get('projection') != 'mitchell_1870_affine_28fit_8check':
                continue
            points = [feature['point']] if 'point' in feature else feature.get('points', feature.get('polygon'))
            pixels = [raw] if 'point' in feature else raw
            if len(points) != len(pixels):
                raise ValueError('Geometry/pixel count differs: ' + feature['id'])
            for pixel, point in zip(pixels, points):
                if math.dist(project(pixel, result['coefficients']), point) > 0.008:
                    raise ValueError('Reprojected geometry differs: ' + feature['id'])
            if 'axis_points' in feature:
                axis_pixels = feature.get('source_axis_pixels', [])
                if len(axis_pixels) != len(feature['axis_points']) or len(axis_pixels) < 2:
                    raise ValueError('Bridge axis has no complete source reading: ' + feature['id'])
                for pixel, point in zip(axis_pixels, feature['axis_points']):
                    if math.dist(project(pixel, result['coefficients']), point) > 0.008:
                        raise ValueError('Reprojected bridge axis differs: ' + feature['id'])
            count += 1
    if len(plan['shoreline_source_pixels']) != len(plan['shoreline'][1:-1]):
        raise ValueError('Shoreline/source pixel count differs')
    for pixel, point in zip(plan['shoreline_source_pixels'], plan['shoreline'][1:-1]):
        if math.dist(project(pixel, result['coefficients']), point) > 0.008:
            raise ValueError('Reprojected shoreline differs')
    print(f"PASS: {len(fit_controls)} fit controls, training RMS {result['rms_m']:.2f} m; "
          f"{len(checks)} reserved checks, RMS {result['held_out_rms_m']:.2f} m, max {result['held_out_max_m']:.2f} m.")
    print(f'Raster, control provenance, {count} projected features and shoreline match. No check point anchors geometry.')
    print(f"Portable OSM targets: {target_check['portable_targets']} checked from {target_check['portable_ways']} ways / {target_check['portable_nodes']} nodes; CRS rounding error < {target_check['max_rounding_error_m']:.4f} m.")
    print('Intersection registration is not parcel or bank accuracy. See the separate model/uncertainty audit.')


if __name__ == '__main__':
    main()
