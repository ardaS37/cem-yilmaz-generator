"""Image rendering functions used by the meme editor."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE = PROJECT_DIR / "images" / "cmorjinal.jpg"
SIDE_STRIP = PROJECT_DIR / "assets" / "bpt-haber-sol-serit.png"
OUTPUT_SIZE = (720, 1012)


def _cover(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """Resize and center-crop an image to exactly fit the poster."""
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _tint_layer(color: tuple[int, int, int], opacity: int, size: Tuple[int, int]) -> Image.Image:
    """Create a gentle top-to-bottom news-card colour layer."""
    width, height = size
    layer = Image.new("RGBA", size)
    pixels = layer.load()
    for y in range(height):
        progress = y / max(height - 1, 1)
        alpha = int(opacity * (0.45 + progress * 0.55))
        for x in range(width):
            pixels[x, y] = (*color, alpha)
    return layer


def parse_hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("Renk 6 haneli hex olmalı; örnek: #2436B9")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _face_warp(image: Image.Image, bulge: int, squish: int, swirl: int) -> Image.Image:
    """Warp the central portrait area; tuned for close-up face photographs."""
    if not any((bulge, squish, swirl)):
        return image
    pixels = np.asarray(image)
    height, width = pixels.shape[:2]
    yy, xx = np.mgrid[0:height, 0:width]
    center_x, center_y = width * 0.5, height * 0.47
    dx = (xx - center_x) / (width * 0.38)
    dy = (yy - center_y) / (height * 0.32)
    radius = np.sqrt(dx * dx + dy * dy)
    mask = radius < 1
    angle = np.arctan2(dy, dx) - np.deg2rad(swirl) * (1 - np.minimum(radius, 1)) ** 2
    # Positive bulge samples farther from the centre, making the face look rounder.
    source_radius = radius * (1 + (bulge / 100) * (1 - np.minimum(radius, 1)) ** 2)
    source_x = center_x + np.cos(angle) * source_radius * width * 0.38
    # Positive values compress the face vertically; negative values stretch it.
    source_y = center_y + np.sin(angle) * source_radius * height * 0.32 * (1 + squish / 160)
    sx = np.clip(np.rint(source_x).astype(int), 0, width - 1)
    sy = np.clip(np.rint(source_y).astype(int), 0, height - 1)
    result = pixels.copy()
    result[mask] = pixels[sy[mask], sx[mask]]
    return Image.fromarray(result)


def _global_squash(image: Image.Image, horizontal: int, vertical: int) -> Image.Image:
    """Compress or stretch the entire frame around its centre, not just the face."""
    if not any((horizontal, vertical)):
        return image
    width, height = image.size
    horizontal_factor = max(0.25, 1 + horizontal / 100)
    vertical_factor = max(0.25, 1 + vertical / 100)
    return image.transform(
        (width, height), Image.Transform.AFFINE,
        (horizontal_factor, 0, width * (1 - horizontal_factor) / 2, 0, vertical_factor, height * (1 - vertical_factor) / 2),
        resample=Image.Resampling.BICUBIC,
    )


def _apply_extra_effects(
    image: Image.Image, sepia: int, posterize: int, pixelate: int, edges: int, grain: int,
    rgb_shift: int, vignette: int, scanlines: int, emboss: bool, mirror: bool,
) -> Image.Image:
    if mirror:
        image = ImageOps.mirror(image)
    if sepia:
        gray = ImageOps.grayscale(image)
        warm = ImageOps.colorize(gray, "#24150B", "#F4D7A1")
        image = Image.blend(image, warm, sepia / 100)
    if posterize < 8:
        image = ImageOps.posterize(image, posterize)
    if pixelate > 1:
        width, height = image.size
        small = image.resize((max(1, width // pixelate), max(1, height // pixelate)), Image.Resampling.NEAREST)
        image = small.resize((width, height), Image.Resampling.NEAREST)
    if edges:
        outlines = image.filter(ImageFilter.FIND_EDGES)
        image = Image.blend(image, outlines, edges / 100)
    if emboss:
        image = ImageChops.screen(image, image.filter(ImageFilter.EMBOSS))
    array = np.asarray(image).astype(np.float32)
    height, width = array.shape[:2]
    if rgb_shift:
        shifted = array.copy()
        shifted[:, :, 0] = np.roll(array[:, :, 0], rgb_shift, axis=1)
        shifted[:, :, 2] = np.roll(array[:, :, 2], -rgb_shift, axis=1)
        array = shifted
    if grain:
        noise = np.random.default_rng(2026).normal(0, grain * 0.9, array.shape[:2])[:, :, None]
        array += noise
    if vignette:
        yy, xx = np.mgrid[0:height, 0:width]
        distance = np.sqrt(((xx - width / 2) / (width / 2)) ** 2 + ((yy - height / 2) / (height / 2)) ** 2)
        array *= (1 - np.clip(distance, 0, 1)[:, :, None] * vignette / 150)
    if scanlines:
        array[::4] *= 1 - scanlines / 160
    return Image.fromarray(np.uint8(np.clip(array, 0, 255)))


def _add_side_strip(image: Image.Image) -> Image.Image:
    """Place the extracted BPT news strip along the left edge of the poster."""
    if not SIDE_STRIP.exists():
        return image
    with Image.open(SIDE_STRIP) as opened:
        strip = opened.convert("RGBA")
    width = round(strip.width * image.height / strip.height)
    strip = strip.resize((width, image.height), Image.Resampling.LANCZOS)
    result = image.convert("RGBA")
    result.alpha_composite(strip, (0, 0))
    return result.convert("RGB")


def render_poster(
    image_path: Optional[str], text: str, tint_hex: str = "#2436B9", tint_opacity: int = 115,
    brightness: int = 100, contrast: int = 115, saturation: int = 35, blur: int = 0, sharpness: int = 100,
    horizontal_squash: int = 0, vertical_squash: int = 0, swirl: int = 0, negative: bool = False, glow: int = 0,
    sepia: int = 0, posterize: int = 8, pixelate: int = 1, edges: int = 0, grain: int = 0,
    rgb_shift: int = 0, vignette: int = 0, scanlines: int = 0, emboss: bool = False, mirror: bool = False,
    text_glow: int = 0, text_glow_hex: str = "#55CCFF", text_rgb: bool = False,
    side_strip: bool = False,
) -> Image.Image:
    """Build the final poster and return it as an RGB Pillow image."""
    source = Path(image_path) if image_path else DEFAULT_IMAGE
    with Image.open(source) as opened:
        image = _cover(opened, OUTPUT_SIZE)
    image = ImageEnhance.Brightness(image).enhance(brightness / 100)
    image = ImageEnhance.Contrast(image).enhance(contrast / 100)
    image = ImageEnhance.Color(image).enhance(saturation / 100)
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    image = ImageEnhance.Sharpness(image).enhance(sharpness / 100)
    image = _global_squash(image, horizontal_squash, vertical_squash)
    image = _face_warp(image, 0, 0, swirl)
    if negative:
        image = ImageOps.invert(image)
    if glow:
        bright = ImageEnhance.Brightness(image).enhance(1 + glow / 45)
        image = ImageChops.screen(image, bright.filter(ImageFilter.GaussianBlur(radius=max(1, glow // 32))))
    image = _apply_extra_effects(image, sepia, posterize, pixelate, edges, grain, rgb_shift, vignette, scanlines, emboss, mirror)
    tinted = Image.alpha_composite(image.convert("RGBA"), _tint_layer(parse_hex_color(tint_hex), tint_opacity, OUTPUT_SIZE))
    if side_strip:
        tinted = _add_side_strip(tinted).convert("RGBA")
    draw = ImageDraw.Draw(tinted)
    font = _font(39)
    # Match the reference news-card layout: just below the chin, slightly left aligned.
    text_x = int(OUTPUT_SIZE[0] * (0.14 if side_strip else 0.075))
    lines = _wrap_text(draw, text.strip(), font, OUTPUT_SIZE[0] - text_x - 40)
    line_height = 52
    y = int(OUTPUT_SIZE[1] * 0.655)
    text_positions = []
    for line in lines:
        text_positions.append((text_x, y, line))
        y += line_height
    if text_glow:
        glow_layer = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_color = parse_hex_color(text_glow_hex)
        for x, text_y, line in text_positions:
            glow_draw.text((x, text_y), line, font=font, fill=(*glow_color, min(255, text_glow * 3)))
        radius = max(2, text_glow // 8)
        tinted = Image.alpha_composite(tinted, glow_layer.filter(ImageFilter.GaussianBlur(radius=radius)))
        draw = ImageDraw.Draw(tinted)
    for x, text_y, line in text_positions:
        if text_rgb:
            draw.text((x - 3, text_y), line, font=font, fill=(255, 40, 80, 210))
            draw.text((x + 3, text_y), line, font=font, fill=(40, 180, 255, 210))
        draw.text((x, text_y), line, font=font, fill="white")
    return tinted.convert("RGB")
