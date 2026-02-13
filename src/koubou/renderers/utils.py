"""Shared utilities for renderers."""

import math
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter


def parse_color(hex_color: str) -> Tuple[int, ...]:
    """Parse hex color string to RGBA tuple."""
    color = hex_color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    if len(color) == 6:
        color += "ff"
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4, 6))


def resolve_value(value: str, dimension: int) -> int:
    """Convert percentage or pixel string to pixel value."""
    if value.endswith("%"):
        return int(dimension * float(value[:-1]) / 100.0)
    return int(value)


def draw_shadow(
    canvas_size: Tuple[int, int],
    shape: str,
    bbox: Tuple[int, int, int, int],
    shadow_color: str = "#00000040",
    shadow_blur: int = 15,
    shadow_offset: Tuple[int, int] = (0, 6),
    corner_radius: int = 16,
) -> Image.Image:
    """Create a shadow layer for a shape.

    Returns an RGBA image with the blurred shadow ready for compositing.
    """
    color = parse_color(shadow_color)
    x0, y0, x1, y1 = bbox
    ox, oy = shadow_offset

    shadow = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)

    shifted_bbox = [x0 + ox, y0 + oy, x1 + ox, y1 + oy]

    if shape == "circle":
        draw.ellipse(shifted_bbox, fill=color)
    elif shape == "rounded_rect":
        draw.rounded_rectangle(shifted_bbox, radius=corner_radius, fill=color)
    else:
        draw.rectangle(shifted_bbox, fill=color)

    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    return shadow


def draw_shape_aa(
    canvas_size: Tuple[int, int],
    shape: str,
    bbox: Tuple[int, int, int, int],
    fill: Optional[Tuple[int, ...]] = None,
    outline: Optional[Tuple[int, ...]] = None,
    width: int = 0,
    corner_radius: int = 16,
    scale: int = 2,
) -> Image.Image:
    """Draw a shape with anti-aliasing via supersampling.

    Renders at `scale`x resolution then downscales with LANCZOS for smooth edges.
    Returns an RGBA image at the original canvas_size.
    """
    cw, ch = canvas_size
    sw, sh = cw * scale, ch * scale

    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    x0, y0, x1, y1 = bbox
    scaled_bbox = [x0 * scale, y0 * scale, x1 * scale, y1 * scale]
    scaled_width = width * scale
    scaled_radius = corner_radius * scale

    if shape == "circle":
        draw.ellipse(scaled_bbox, fill=fill, outline=outline, width=scaled_width)
    elif shape == "rounded_rect":
        draw.rounded_rectangle(
            scaled_bbox,
            radius=scaled_radius,
            fill=fill,
            outline=outline,
            width=scaled_width,
        )
    else:
        draw.rectangle(scaled_bbox, fill=fill, outline=outline, width=scaled_width)

    return layer.resize(canvas_size, Image.Resampling.LANCZOS)


def draw_shape_mask_aa(
    size: Tuple[int, int],
    shape: str,
    corner_radius: int = 16,
    scale: int = 2,
) -> Image.Image:
    """Create an anti-aliased shape mask (L mode) at the given size."""
    w, h = size
    sw, sh = w * scale, h * scale

    mask = Image.new("L", (sw, sh), 0)
    draw = ImageDraw.Draw(mask)

    if shape == "circle":
        draw.ellipse([0, 0, sw - 1, sh - 1], fill=255)
    elif shape == "rounded_rect":
        draw.rounded_rectangle(
            [0, 0, sw - 1, sh - 1], radius=corner_radius * scale, fill=255
        )
    else:
        draw.rectangle([0, 0, sw - 1, sh - 1], fill=255)

    return mask.resize(size, Image.Resampling.LANCZOS)


def compute_bezier_points(
    p0: Tuple[int, int],
    p1: Tuple[int, int],
    bow_factor: float = 0.3,
    num_points: int = 30,
) -> List[Tuple[int, int]]:
    """Compute points along a quadratic Bezier curve.

    The control point is offset perpendicular to the direct path between p0 and p1.
    """
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return [p0, p1]

    mid_x = (p0[0] + p1[0]) / 2
    mid_y = (p0[1] + p1[1]) / 2

    # Perpendicular direction
    nx = -dy / length
    ny = dx / length

    offset = length * bow_factor
    cx = mid_x + nx * offset
    cy = mid_y + ny * offset

    points = []
    for i in range(num_points + 1):
        t = i / num_points
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t**2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t**2 * p1[1]
        points.append((int(x), int(y)))
    return points


def compute_facing_connector_points(
    src_bbox: Tuple[int, int, int, int],
    disp_bbox: Tuple[int, int, int, int],
) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """Compute the 4 points for a facing/funnel connector.

    Returns (src_pt1, src_pt2, disp_pt1, disp_pt2) where:
    - src_pt1/pt2 are on the nearest edge of the source bbox
    - disp_pt1/pt2 are on the nearest edge of the display bbox
    """
    sx0, sy0, sx1, sy1 = src_bbox
    dx0, dy0, dx1, dy1 = disp_bbox

    src_cx = (sx0 + sx1) / 2
    src_cy = (sy0 + sy1) / 2
    disp_cx = (dx0 + dx1) / 2
    disp_cy = (dy0 + dy1) / 2

    diff_x = disp_cx - src_cx
    diff_y = disp_cy - src_cy

    # Determine dominant direction
    if abs(diff_x) > abs(diff_y):
        # Horizontal: connect left/right edges
        if diff_x > 0:
            # Display is to the right of source
            src_pts = ((sx1, sy0), (sx1, sy1))
            disp_pts = ((dx0, dy0), (dx0, dy1))
        else:
            src_pts = ((sx0, sy0), (sx0, sy1))
            disp_pts = ((dx1, dy0), (dx1, dy1))
    else:
        # Vertical: connect top/bottom edges
        if diff_y > 0:
            # Display is below source
            src_pts = ((sx0, sy1), (sx1, sy1))
            disp_pts = ((dx0, dy0), (dx1, dy0))
        else:
            src_pts = ((sx0, sy0), (sx1, sy0))
            disp_pts = ((dx0, dy1), (dx1, dy1))

    return (src_pts[0], src_pts[1], disp_pts[0], disp_pts[1])
