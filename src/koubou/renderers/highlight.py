"""Highlight annotation renderer for screenshots."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from ..exceptions import HighlightRenderError

logger = logging.getLogger(__name__)


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


class HighlightRenderer:
    """Renders highlight annotations (circle, rounded_rect, rect) on screenshots."""

    def render(self, config: dict, canvas: Image.Image) -> None:
        try:
            self._render_highlight(config, canvas)
        except Exception as e:
            raise HighlightRenderError(f"Failed to render highlight: {e}") from e

    def _render_highlight(self, config: dict, canvas: Image.Image) -> None:
        canvas_w, canvas_h = canvas.size
        shape = config["shape"]

        # Resolve center position
        pos = config.get("position", ("50%", "50%"))
        cx = resolve_value(pos[0], canvas_w)
        cy = resolve_value(pos[1], canvas_h)

        # Resolve dimensions
        dims = config.get("dimensions", ("10%", "10%"))
        w = resolve_value(dims[0], canvas_w)
        h = resolve_value(dims[1], canvas_h)

        # Colors
        border_color: Optional[Tuple[int, ...]] = None
        border_width = config.get("border_width", 3)
        if config.get("border_color"):
            border_color = parse_color(config["border_color"])

        fill_color: Optional[Tuple[int, ...]] = None
        if config.get("fill_color"):
            fill_color = parse_color(config["fill_color"])

        corner_radius = config.get("corner_radius", 16)

        # Bounding box from center + dimensions
        x0 = cx - w // 2
        y0 = cy - h // 2
        x1 = cx + w // 2
        y1 = cy + h // 2

        # Draw on transparent overlay
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        outline = border_color if border_color else None
        fill = fill_color if fill_color else None
        width = border_width if outline else 0

        if shape == "circle":
            draw.ellipse([x0, y0, x1, y1], fill=fill, outline=outline, width=width)
        elif shape == "rounded_rect":
            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=corner_radius,
                fill=fill,
                outline=outline,
                width=width,
            )
        elif shape == "rect":
            draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)

        logger.info(f"Rendered {shape} highlight at ({cx},{cy}) size {w}x{h}")

        # Composite overlay onto canvas in place
        composited = Image.alpha_composite(canvas, overlay)
        canvas.paste(composited)
