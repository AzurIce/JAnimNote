import os

import moderngl as mgl
from PIL import Image

from janim.render.base import Renderer
from janim.utils.file_ops import find_file

filepath_to_img_map: dict[str, Image.Image] = {}


def get_img_from_file(file_path: str) -> Image.Image:
    file_path = find_file(file_path)
    mtime = os.path.getmtime(file_path)
    key = (file_path, mtime)

    img = filepath_to_img_map.get(key, None)
    if img is not None:
        return img
    img = Image.open(file_path).convert('RGBA')
    filepath_to_img_map[key] = img
    return img


img_to_texture_map: dict[int, mgl.Texture] = {}


def get_texture_from_img(img: Image.Image) -> mgl.Texture:
    texture = img_to_texture_map.get(id(img), None)
    if texture is not None:
        return texture
    ctx = Renderer.data_ctx.get().ctx
    texture = ctx.texture(
        size=img.size,
        components=len(img.getbands()),
        data=img.tobytes()
    )
    img_to_texture_map[id(img)] = texture
    return texture
