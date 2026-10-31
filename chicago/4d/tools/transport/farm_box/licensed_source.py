# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the credited immutable source without running downloaded code."""
from pathlib import Path
import hashlib
import json
import struct

import numpy as np

SOURCE_SHA256 = '13600b73c1777545e1454d452c58d141469f031b2c5e6c29b1c6fdefe9145046'


def fixed_matmul(left, right):
    """Small source/adaptation transforms with a fixed accumulation order.

    Separate NumPy multiplication/addition operations avoid BLAS dispatch and
    fused accumulation changing exact serialized exports between CPU families.
    """
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    vector = right.ndim == 1
    if vector:
        right = right[:, None]
    result = np.zeros((left.shape[0], right.shape[1]), dtype=np.float64)
    for k in range(left.shape[1]):
        result += left[:, k, None]*right[k, :]
    return result[:, 0] if vector else result


class Source:
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        if hashlib.sha256(self.raw).hexdigest() != SOURCE_SHA256:
            raise ValueError('The credited original source changed')
        if struct.unpack_from('<III', self.raw) != (0x46546c67, 2, len(self.raw)):
            raise ValueError('Invalid original GLB2')
        size, kind = struct.unpack_from('<II', self.raw, 12)
        if kind != 0x4e4f534a:
            raise ValueError('Missing original JSON')
        self.gltf = json.loads(self.raw[20:20+size])
        length, kind = struct.unpack_from('<II', self.raw, 20+size)
        self.binary = self.raw[28+size:]
        if kind != 0x004e4942 or length != len(self.binary):
            raise ValueError('Original binary chunk bounds')
        self.parents = {c: i for i, n in enumerate(self.gltf['nodes']) for c in n.get('children', [])}
        self.worlds = {}
        self.component_cache = {}

    def world(self, index):
        if index not in self.worlds:
            n = self.gltf['nodes'][index]
            if any(k in n for k in ['translation', 'rotation', 'scale']):
                raise ValueError('Unexpected original TRS; review the source contract')
            matrix = np.array(n.get('matrix', np.eye(4).T.reshape(-1).tolist()), dtype=np.float64).reshape(4, 4).T
            self.worlds[index] = fixed_matmul(self.world(self.parents[index]) if index in self.parents else np.eye(4), matrix)
        return self.worlds[index]

    def accessor(self, index):
        a = self.gltf['accessors'][index]
        v = self.gltf['bufferViews'][a['bufferView']]
        if 'sparse' in a:
            raise ValueError('Unexpected original storage; explicit source review required')
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[a['componentType']]
        width = {'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'SCALAR': 1}[a['type']]
        element = np.dtype(dtype).itemsize
        stride = v.get('byteStride', width*element)
        relative = a.get('byteOffset', 0)
        if stride < width*element or stride % element or relative+(a['count']-1)*stride+width*element > v['byteLength']:
            raise ValueError('Original accessor escapes its declared view')
        return np.ndarray((a['count'], width),dtype=dtype,buffer=self.binary,
                          offset=v.get('byteOffset', 0)+relative,
                          strides=(stride,element)).copy()

    def primitive(self, node):
        return self.gltf['meshes'][self.gltf['nodes'][node]['mesh']]['primitives'][0]

    def positions(self, node):
        points = self.accessor(self.primitive(node)['attributes']['POSITION'])
        return (fixed_matmul(np.c_[points, np.ones(len(points))], self.world(node).T))[:, :3]

    def world_directions(self, node, attribute):
        original = self.accessor(self.primitive(node)['attributes'][attribute])
        matrix = self.world(node)[:3, :3]
        xyz = fixed_matmul(original[:, :3], np.linalg.inv(matrix) if attribute == 'NORMAL' else matrix.T)
        xyz /= np.linalg.norm(xyz, axis=1)[:, None]
        return xyz if original.shape[1] == 3 else np.c_[xyz, original[:, 3]]

    def components(self, node):
        """Stable connected surface pieces, with original triangle/UV ownership.

        Welding is only an analysis index at1e-4 original units; no original
        positions, indices, normals or UVs are modified by this classification.
        """
        if node in self.component_cache:
            return self.component_cache[node]
        vertices = self.positions(node)
        faces = self.accessor(self.primitive(node)['indices']).reshape(-1, 3)
        parent = list(range(len(vertices)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def join(a, b):
            a, b = find(a), find(b)
            if a != b:
                parent[b] = a

        seen = {}
        for i, p in enumerate(vertices):
            key = tuple(np.rint(p*1e4).astype(np.int64))
            join(i, seen.setdefault(key, i))
        for a, b, c in faces:
            join(int(a), int(b))
            join(int(a), int(c))
        groups = {}
        for i, face in enumerate(faces):
            groups.setdefault(find(int(face[0])), []).append(i)
        result = []
        for triangle_rows in groups.values():
            ids = faces[triangle_rows].reshape(-1)
            points = vertices[np.unique(ids)]
            result.append({'indices': ids, 'triangles': len(triangle_rows),
                           'min': points.min(axis=0), 'max': points.max(axis=0)})
        self.component_cache[node] = result
        return result
