from __future__ import annotations

import base64
import hashlib
import io
import logging
import re
from pathlib import Path

import edge_tts
import numpy as np
import trimesh
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
app = FastAPI(title="Ruang Dongeng", docs_url="/api/docs")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
logger = logging.getLogger("ruang_dongeng")


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    voice: str = Field(default="id-ID-GadisNeural", pattern=r"^id-ID-(Gadis|Ardi)Neural$")
    rate: float = Field(default=0.92, ge=0.75, le=1.15)
    pitch: float = Field(default=1.04, ge=0.8, le=1.3)


class ModelRequest(BaseModel):
    title: str = Field(default="Dongeng Ajaib", min_length=1, max_length=80)
    cover: str | None = Field(default=None, max_length=7_000_000)


def make_cover(title: str, data_url: str | None) -> Image.Image:
    image = Image.new("RGB", (768, 1024), "#2c7776")
    draw = ImageDraw.Draw(image)
    for y in range(1024):
        t = y / 1024
        color = (int(89 - 33 * t), int(191 - 79 * t), int(166 - 35 * t))
        draw.line((0, y, 768, y), fill=color)
    draw.rounded_rectangle((24, 24, 744, 1000), radius=35, outline="#ffe2a0", width=12)
    font_path = Path("C:/Windows/Fonts/arialbd.ttf")
    font = ImageFont.truetype(str(font_path), 53) if font_path.exists() else ImageFont.load_default(size=53)
    title_lines = []
    line = ""
    for word in title.upper().split():
        proposal = f"{line} {word}".strip()
        if draw.textbbox((0, 0), proposal, font=font)[2] > 650 and line:
            title_lines.append(line)
            line = word
        else:
            line = proposal
    if line:
        title_lines.append(line)
    y = 150
    for row in title_lines[:3]:
        bounds = draw.textbbox((0, 0), row, font=font)
        draw.text(((768 - (bounds[2] - bounds[0])) / 2, y), row, font=font, fill="#fff3ce", stroke_width=2, stroke_fill="#28556b")
        y += 78

    if data_url:
        try:
            raw = data_url.split(",", 1)[1] if "," in data_url else data_url
            uploaded = Image.open(io.BytesIO(base64.b64decode(raw, validate=True))).convert("RGB")
            uploaded.thumbnail((540, 490))
            x = (768 - uploaded.width) // 2
            y_img = max(420, min(540, y + 45))
            image.paste(uploaded, (x, y_img))
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Gambar sampul tidak bisa dibaca.") from exc
    else:
        draw.ellipse((235, 460, 533, 758), fill="#f6d990", outline="#fff1c4", width=9)
        draw.regular_polygon((384, 610, 68), num_sides=5, rotation=0, fill="#805b91")
    draw.text((384, 950), "CERITA SEBELUM TIDUR", anchor="mm", fill="#ffe2a0", font=font)
    return image


def make_book_glb(title: str, cover: str | None) -> bytes:
    width, height, thickness = 3.25, 4.35, 0.3
    scene = trimesh.Scene()

    def box(name: str, extents: tuple[float, float, float], color: tuple[int, int, int, int], center: tuple[float, float, float]) -> None:
        mesh = trimesh.creation.box(extents=extents)
        mesh.visual.face_colors = color
        mesh.apply_translation(center)
        scene.add_geometry(mesh, geom_name=name, node_name=name)

    box("paper_block", (width - 0.09, height - 0.09, thickness), (250, 241, 216, 255), (0, 0, 0))
    box("back_hardcover", (width + 0.1, height + 0.1, 0.16), (37, 89, 102, 255), (0, 0, -0.24))
    box("front_hardcover", (width + 0.1, height + 0.1, 0.16), (39, 119, 116, 255), (0, 0, 0.22))
    box("spine", (0.19, height + 0.1, 0.43), (27, 81, 95, 255), (-width / 2, 0, 0))
    for offset in (-0.125, -0.075, -0.025, 0.025, 0.075):
        box(f"page_ridge_{str(offset).replace('-', 'm').replace('.', '_')}", (width - 0.12, height - 0.1, 0.008), (255, 249, 231, 255), (0, 0, offset))

    art = make_cover(title, cover)
    verts = np.array([
        [-width / 2 + 0.08, -height / 2 + 0.08, 0.305],
        [width / 2 - 0.08, -height / 2 + 0.08, 0.305],
        [width / 2 - 0.08, height / 2 - 0.08, 0.305],
        [-width / 2 + 0.08, height / 2 - 0.08, 0.305],
    ])
    face = trimesh.Trimesh(vertices=verts, faces=np.array([[0, 1, 2], [0, 2, 3]]), process=False)
    material = trimesh.visual.material.SimpleMaterial(image=art, diffuse=(255, 255, 255, 255))
    face.visual = trimesh.visual.texture.TextureVisuals(uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]]), material=material)
    scene.add_geometry(face, geom_name="cover_art", node_name="cover_art")

    inner = Image.new("RGB", (768, 1024), "#fff7e3")
    inside_draw = ImageDraw.Draw(inner)
    inside_draw.rounded_rectangle((24, 24, 744, 1000), radius=35, outline="#dcc9a3", width=10)
    inside_font_path = Path("C:/Windows/Fonts/arialbd.ttf")
    inside_font = ImageFont.truetype(str(inside_font_path), 34) if inside_font_path.exists() else ImageFont.load_default(size=34)
    inside_draw.text((384, 440), title[:34], anchor="mm", fill="#9d5276", font=inside_font)
    inside_draw.text((384, 535), "Mulai membaca...", anchor="mm", fill="#6b5668", font=inside_font)
    inside_verts = verts.copy()
    inside_verts[:, 2] = 0.13
    back_face = trimesh.Trimesh(vertices=inside_verts, faces=np.array([[2, 1, 0], [3, 2, 0]]), process=False)
    inner_material = trimesh.visual.material.SimpleMaterial(image=inner, diffuse=(255, 255, 255, 255))
    back_face.visual = trimesh.visual.texture.TextureVisuals(uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]]), material=inner_material)
    scene.add_geometry(back_face, geom_name="cover_inner", node_name="cover_inner")
    return scene.export(file_type="glb")


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.post("/api/tts")
async def synthesize(request: SpeechRequest) -> Response:
    clean_text = re.sub(r"\[BOOM\]", "", request.text, flags=re.IGNORECASE).strip()
    if not clean_text:
        raise HTTPException(status_code=422, detail="Teks cerita kosong.")
    rate = f"{round((request.rate - 1) * 100):+d}%"
    pitch_hz = round((request.pitch - 1) * 45)
    pitch = f"{pitch_hz:+d}Hz"
    try:
        communicator = edge_tts.Communicate(clean_text, request.voice, rate=rate, pitch=pitch)
        chunks = bytearray()
        async for item in communicator.stream():
            if item["type"] == "audio":
                chunks.extend(item["data"])
        if not chunks:
            raise RuntimeError("TTS returned no audio")
        return Response(bytes(chunks), media_type="audio/mpeg", headers={"Cache-Control": "no-store"})
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Layanan suara neural tidak tersedia. Coba lagi saat internet tersambung.") from exc


@app.post("/api/model")
async def model(request: ModelRequest) -> Response:
    try:
        cache_key = hashlib.sha256((request.title + "\0" + (request.cover or "")).encode("utf-8")).hexdigest()
        target = ROOT / "generated" / f"{cache_key}.glb"
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(make_book_glb(request.title, request.cover))
        return FileResponse(target, media_type="model/gltf-binary", headers={"Cache-Control": "no-store"})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Model buku GLB gagal dibuat")
        raise HTTPException(status_code=500, detail=f"Model buku gagal: {type(exc).__name__}: {exc}") from exc

