from typing import List, Tuple
from enum import IntEnum
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LensProjection:
    fov_s: float
    """Phi size of the panorama face."""
    fov_h: float
    """Theta size of the panorama face."""
    k2: float  #:
    k3: float  #:
    k4: float  #:
    cx: float
    """Theta offset."""
    cy: float
    """Phi offset."""
    lx: float  #:
    ly: float  #:


@dataclass
class OrientedPosition:
    """Position and rotation of a panorama face in the scene. Angles are in radians."""
    x: float  #:
    y: float  #:
    z: float  #:
    yaw: float  #:
    pitch: float  #:
    roll: float  #:


@dataclass
class CameraMetadata:
    lens_projection: LensProjection
    position: OrientedPosition


@dataclass
class LookAroundPano:
    pano_id: int

    build_id: int

    lat: float

    lon: float

    raw_orientation: Tuple[int, int, int]

    tile: Tuple[int, int, int] = None

    camera_metadata: List[CameraMetadata] = None


@dataclass
class CoverageTile:
    """Represents a coverage tile."""
    x: int
    """The X coordinate of the tile at z=17."""
    y: int
    """The Y coordinate of the tile at z=17."""
    panos: List[LookAroundPano]
    """Panoramas on this tile."""
    last_modified: datetime


class Face(IntEnum):
    """
    Face indices of a Look Around panorama.
    """
    BACK = 0,  #:
    LEFT = 1,  #:
    FRONT = 2,  #:
    RIGHT = 3,  #:
    TOP = 4,  #:
    BOTTOM = 5  #:
