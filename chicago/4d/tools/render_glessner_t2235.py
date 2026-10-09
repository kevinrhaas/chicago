"""Repeatable actual-GLB courtyard, rear and street review for T-2235.

Run with pinned Blender like render_structure_review.py; use --cameras
courtyard-west,stable-south,courtyard-west-roof,west,northwest,west-street.
No meshes, materials, or background buildings are hidden. The courtyard and
rear cameras expose the full ridge and projecting eave; the west and northwest
cameras retain the earlier photo comparison viewpoints.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_structure_review as review

review.CAMERAS.update({
    'west': {'position': (-150, 13.4493, 6.3),
             'target': (0, 13.4493, 6.3), 'lens': 200},
    'northwest': {'position': (-25, 48, 2.0),
                  'target': (10, 20, 6.3), 'lens': 40},
    'west-street': {'position': (-28, 13.4493, 1.7),
                    'target': (0, 13.4493, 6.0), 'lens': 36},
})
review.CAMERAS['courtyard-west'] = {'position': (33, 0, 2), 'target': (9, 14, 7), 'lens': 32}
review.main()
