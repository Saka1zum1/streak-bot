import math
from io import BytesIO
from typing import Tuple, Union
import gc
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.ndimage import map_coordinates
from requests import Session
from aiohttp import ClientSession
from PIL import Image
from pillow_heif import register_heif_opener

import GroundMetadataTile_pb2
from auth import Authenticator
from dataClass import (
    LensProjection,
    OrientedPosition,
    CameraMetadata,
    LookAroundPano,
    Face,
)

COVERAGE_TILE_ENDPOINT = "https://gspe76-ssl.ls.apple.com/api/tile?"
FACE_ENDPOINT = "https://gspe72-ssl.ls.apple.com/mnn_us/"
register_heif_opener()


def tile_coord_to_wgs84(x: float, y: float, zoom: int) -> Tuple[float, float]:
    scale = 1 << zoom
    lon_deg = x / scale * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / scale)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def wgs84_to_tile_coord(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    lat_rad = math.radians(lat)
    scale = 1 << zoom
    x = (lon + 180.0) / 360.0 * scale
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * scale
    return int(x), int(y)


def _build_coverage_tile_request_headers(tile_x: int, tile_y: int) -> dict:
    headers = {
        "maps-tile-style": "style=57&size=2&scale=0&v=0&preflight=2",
        "maps-tile-x": str(tile_x),
        "maps-tile-y": str(tile_y),
        "maps-tile-z": "17",
        "maps-auth-token": "w31CPGRO/n7BsFPh8X7kZnFG0LDj9pAuR8nTtH3xhH8=",
    }
    return headers


def protobuf_tile_offset_to_wgs84(x_offset: int, y_offset: int, tile_x: int, tile_y: int) \
        -> Tuple[float, float]:
    TILE_SIZE = 256
    pano_x = tile_x + (x_offset / 64.0) / (TILE_SIZE - 1)
    pano_y = tile_y + (255 - (y_offset / 64.0)) / (TILE_SIZE - 1)
    lat, lon = tile_coord_to_wgs84(pano_x, pano_y, 17)
    return lat, lon


def convert_pano_orientation(lat: float, lon: float, raw_yaw: int, raw_pitch: int, raw_roll: int) \
        -> Tuple[float, float, float]:
    yaw = (raw_yaw / 16383.0) * math.tau
    pitch = (raw_pitch / 16383.0) * math.tau
    roll = (raw_roll / 16383.0) * math.tau

    rot = Rotation.from_euler("xyz", (yaw, pitch, roll))
    rot *= Rotation.from_quat((0.5, 0.5, -0.5, -0.5))
    quat = rot.as_quat()
    quat2 = quat[3], -quat[2], -quat[0], quat[1]
    conv_roll, conv_pitch, conv_yaw = \
        Rotation.from_euler("xyz",
                            _from_rigid_transform_ecef_no_offset(lat, lon, quat2)) \
            .as_euler("zyx")
    return math.degrees(conv_yaw), math.degrees(conv_pitch), math.degrees(conv_roll)


def _from_rigid_transform_ecef_no_offset(lat: float, lon: float, rotation: Tuple[float, float, float, float]) \
        -> Tuple[float, float, float]:
    ecef_basis = _create_local_ecef_basis(lat, lon)
    mult = Rotation.from_matrix(ecef_basis) * Rotation.from_quat(rotation)
    local_rot = mult.as_euler("zxy")
    return local_rot[2], -local_rot[1], -local_rot[0]


def _create_local_ecef_basis(lat: float, lon: float) -> np.ndarray:
    lat = np.radians(lat)
    lon = np.radians(lon)

    cos_lat = np.cos(lat)
    sin_lat = np.sin(lat)
    cos_lon = np.cos(lon)
    sin_lon = np.sin(lon)

    ecef_basis = np.array([
        [-sin_lon, cos_lon, 0],
        [cos_lon * cos_lat, sin_lon * cos_lat, sin_lat],
        [cos_lon * sin_lat, sin_lon * sin_lat, -cos_lat]
    ])
    return ecef_basis


async def get_coverage_tile(tile_x: int, tile_y: int, session: ClientSession = None) \
        -> Tuple[GroundMetadataTile_pb2.GroundMetadataTile, int]:
    headers = _build_coverage_tile_request_headers(tile_x, tile_y)
    async with session.get(COVERAGE_TILE_ENDPOINT, headers=headers) as response:
        content = await response.read()

    etag = response.headers["ETag"]
    etag = int(etag[1:-1])

    tile = GroundMetadataTile_pb2.GroundMetadataTile()
    tile.ParseFromString(content)
    return tile, etag


def _camera_metadata_to_dataclass(camera_metadata_pb: GroundMetadataTile_pb2.CameraMetadata):
    lens_projection_pb = camera_metadata_pb.lens_projection
    position_pb = camera_metadata_pb.position
    return CameraMetadata(
        lens_projection=LensProjection(
            fov_s=lens_projection_pb.fov_s,
            fov_h=lens_projection_pb.fov_h,
            k2=lens_projection_pb.k2,
            k3=lens_projection_pb.k3,
            k4=lens_projection_pb.k4,
            cx=lens_projection_pb.cx,
            cy=lens_projection_pb.cy,
            lx=lens_projection_pb.lx,
            ly=lens_projection_pb.ly,
        ),
        position=OrientedPosition(
            x=position_pb.x,
            y=position_pb.y,
            z=position_pb.z,
            yaw=position_pb.yaw,
            pitch=position_pb.pitch,
            roll=position_pb.roll,
        )
    )


def parse_coverage_tile(tile: GroundMetadataTile_pb2.GroundMetadataTile):
    panos = []
    camera_metadatas = [_camera_metadata_to_dataclass(c) for c in tile.camera_metadata]
    for pano_pb in tile.pano:
        lat, lon = protobuf_tile_offset_to_wgs84(
            pano_pb.tile_position.x,
            pano_pb.tile_position.y,
            tile.tile_coordinate.x,
            tile.tile_coordinate.y)
        pano = LookAroundPano(
            pano_id=pano_pb.panoid,
            build_id=tile.build_table[pano_pb.build_table_idx].build_id,
            lat=lat,
            lon=lon,
            raw_orientation=(pano_pb.tile_position.yaw, pano_pb.tile_position.pitch, pano_pb.tile_position.roll),
            tile=(tile.tile_coordinate.x, tile.tile_coordinate.y, tile.tile_coordinate.z),
            camera_metadata=[camera_metadatas[i] for i in pano_pb.camera_metadata_idx]
        )
        panos.append(pano)
    return panos


async def get_apple_coverage_tile(lat: float, lon: float, session: ClientSession = None):
    tile_x, tile_y = wgs84_to_tile_coord(lat, lon, 17)
    tile, etag = await get_coverage_tile(tile_x, tile_y, session)
    panos = parse_coverage_tile(tile)
    if panos and len(panos) > 0:
        return panos[0]


def _panoid_to_string(pano: Union[LookAroundPano, Tuple[int, int]]) -> Tuple[str, str]:
    if isinstance(pano, LookAroundPano):
        panoid, build_id = str(pano.pano_id), str(pano.build_id)
    else:
        panoid, build_id = str(pano[0]), str(pano[1])

    if len(panoid) > 20:
        raise ValueError("Pano ID must not be longer than 20 digits.")
    if len(build_id) > 10:
        raise ValueError("build_id must not be longer than 10 digits.")

    return panoid, build_id


def get_panorama_face(pano: Union[LookAroundPano, Tuple[int, int]],
                      face: Union[Face, int], zoom: int,
                      auth: Authenticator, session: Session = None) -> bytes:
    panoid, build_id = _panoid_to_string(pano)
    url = _build_panorama_face_url(panoid, build_id, int(face), zoom, auth)
    requester = session if session else requests
    response = requester.get(url)
    if response.status_code != 200:
        raise Exception(f"Error getting apple pano face: {response.status_code} - {response.reason}")
    else:
        return response.content


def get_apple_equ(pano: LookAroundPano, zoom: int, auth: Authenticator, session: Session = None):
    faces = []
    for face in Face:
        face_heic = get_panorama_face(pano, face, zoom, auth, session)
        image = Image.open(BytesIO(face_heic))
        faces.append(image)
    stitched_image = to_equirectangular_np(faces, pano.camera_metadata)
    return np.array(stitched_image)


def _build_panorama_face_url(panoid: str, build_id: str, face: int, zoom: int, auth: Authenticator) -> str:
    zoom = min(7, zoom)
    panoid_padded = panoid.zfill(20)
    panoid_split = [panoid_padded[i:i + 4] for i in range(0, len(panoid_padded), 4)]
    panoid_url = "/".join(panoid_split)
    build_id_padded = build_id.zfill(10)
    url = FACE_ENDPOINT + f"{panoid_url}/{build_id_padded}/t/{face}/{zoom}"
    url = auth.authenticate_url(url)
    return url


def get_rotation_matrix(yaw, pitch, roll):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)

    Ry = np.array([[cy, 0, sy],
                   [0, 1, 0],
                   [-sy, 0, cy]], dtype=np.float32)
    Rx = np.array([[1, 0, 0],
                   [0, cp, -sp],
                   [0, sp, cp]], dtype=np.float32)
    Rz = np.array([[cr, -sr, 0],
                   [sr, cr, 0],
                   [0, 0, 1]], dtype=np.float32)

    return Ry @ Rx @ Rz


def equirectangular_rotate(img: Image.Image, yaw, pitch, roll):
    img_np = np.asarray(img).astype(np.float32)
    H, W = img_np.shape[:2]

    x, y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    theta = (x / W) * 2 * math.pi - math.pi
    phi = (y / H) * math.pi - (math.pi / 2)

    vx = np.cos(phi) * np.sin(theta)
    vy = np.sin(phi)
    vz = np.cos(phi) * np.cos(theta)
    vectors = np.stack([vx, vy, vz], axis=-1).reshape(-1, 3).astype(np.float32)

    R = get_rotation_matrix(yaw, pitch, roll).astype(np.float32)
    vectors_rot = vectors @ R.T
    vx_r, vy_r, vz_r = vectors_rot[:, 0], vectors_rot[:, 1], vectors_rot[:, 2]

    theta_r = np.arctan2(vx_r, vz_r)
    phi_r = np.arcsin(np.clip(vy_r, -1, 1))

    map_x = ((theta_r + math.pi) / (2 * math.pi)) * W
    map_y = ((phi_r + math.pi / 2) / math.pi) * H

    map_x = np.clip(map_x, 0, W - 1)
    map_y = np.clip(map_y, 0, H - 1)

    output = np.zeros_like(img_np, dtype=np.uint8)
    for c in range(img_np.shape[2]):
        channel = img_np[..., c]
        sampled = map_coordinates(channel, [map_y, map_x], order=1, mode='wrap')
        output[..., c] = sampled.reshape(H * W).astype(np.uint8).reshape(H, W)

    del img_np, vectors, vectors_rot, vx_r, vy_r, vz_r, map_x, map_y
    gc.collect()

    return Image.fromarray(output, mode=img.mode)


def project_top_or_bottom_face_np(face: Image.Image, camera_metadata, full_width: int, full_height: int):
    phi_length = camera_metadata.lens_projection.fov_s
    theta_length = camera_metadata.lens_projection.fov_h

    face_width = int(phi_length * (full_height / math.pi))
    face_height = int(theta_length * (full_height / math.pi))

    x = int((full_width - face_width) / 2)
    y = int((full_height - face_height) / 2)

    input_img = Image.new("RGBA", (full_width, full_height), (0, 0, 0, 0))
    scaled_face = face.resize((face_width, face_height), Image.LANCZOS)
    input_img.paste(scaled_face, (x, y))
    del face, scaled_face

    yaw = -camera_metadata.position.yaw
    pitch = camera_metadata.position.pitch
    roll = camera_metadata.position.roll

    reprojected_img = equirectangular_rotate(input_img, yaw, pitch, roll)
    del input_img
    gc.collect()

    return reprojected_img


def paste_side_face_np(face: Image.Image, camera_metadata, full_width: int, full_height: int, stitched: Image.Image):
    phi_start = math.pi + camera_metadata.position.yaw - (camera_metadata.lens_projection.fov_s / 2)
    if phi_start < 0:
        phi_start += 2 * math.pi

    theta_start = (math.pi / 2) - (camera_metadata.lens_projection.fov_h / 2) - camera_metadata.lens_projection.cy
    phi_length = camera_metadata.lens_projection.fov_s
    theta_length = camera_metadata.lens_projection.fov_h

    face_width = int(phi_length * (full_height / math.pi))
    face_height = int(theta_length * (full_height / math.pi))

    x = int(phi_start * (full_height / math.pi))
    y = int(theta_start * (full_height / math.pi))

    scaled_face = face.resize((math.ceil(face_width), math.ceil(face_height)), Image.LANCZOS)
    if scaled_face.mode != "RGBA":
        scaled_face = scaled_face.convert("RGBA")
    mask = scaled_face.split()[-1]

    stitched.paste(scaled_face, (math.ceil(x), math.ceil(y)), mask)
    if x + scaled_face.width > full_width:
        stitched.paste(scaled_face, (math.ceil(x - full_width), math.ceil(y)), mask)

    del face, scaled_face, mask
    gc.collect()


def to_equirectangular_np(faces, camera_metadata_list):
    full_width = round(faces[0].width * (1024 / 5632)) * 16
    full_height = full_width // 2

    stitched = Image.new("RGBA", (full_width, full_height), (0, 0, 0, 0))

    for face_index in range(5, -1, -1):
        if face_index > 3:
            projected = project_top_or_bottom_face_np(faces[face_index], camera_metadata_list[face_index], full_width,
                                                      full_height)
            stitched.alpha_composite(projected)
            del projected
        else:
            paste_side_face_np(faces[face_index], camera_metadata_list[face_index], full_width, full_height, stitched)

    gc.collect()
    return stitched.convert("RGB")
