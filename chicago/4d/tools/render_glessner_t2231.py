"""Repeatable actual-GLB west / northwest review for T-2231.

Run with pinned Blender like render_structure_review.py; use --cameras
west,northwest. No meshes, materials, or background buildings are hidden.
The distant west camera approximates the owner's flattened elevation; the
northwest camera shows the front gable, west return and lower rear together.
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
review.main()
