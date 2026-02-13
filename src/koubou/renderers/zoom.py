"""Zoom callout renderer for screenshots."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from ..exceptions import ZoomRenderError

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


class ZoomRenderer:
    """Renders magnified zoom callout bubbles on screenshots."""

    def render(self, config: dict, canvas: Image.Image) -> None:
        try:
            self._render_zoom(config, canvas)
        except Exception as e:
            raise ZoomRenderError(f"Failed to render zoom callout: {e}") from e

    def _render_zoom(self, config: dict, canvas: Image.Image) -> None:
        canvas_w, canvas_h = canvas.size
        shape = config.get("shape", "circle")

        # Resolve source region
        src_pos = config["source_position"]
        src_cx = resolve_value(src_pos[0], canvas_w)
        src_cy = resolve_value(src_pos[1], canvas_h)

        src_size = config["source_size"]
        src_w = resolve_value(src_size[0], canvas_w)
        src_h = resolve_value(src_size[1], canvas_h)

        # Source crop box
        src_x0 = max(0, src_cx - src_w // 2)
        src_y0 = max(0, src_cy - src_h // 2)
        src_x1 = min(canvas_w, src_cx + src_w // 2)
        src_y1 = min(canvas_h, src_cy + src_h // 2)

        # Resolve display region
        disp_pos = config.get("display_position", ("25%", "25%"))
        disp_cx = resolve_value(disp_pos[0], canvas_w)
        disp_cy = resolve_value(disp_pos[1], canvas_h)

        disp_size = config["display_size"]
        disp_w = resolve_value(disp_size[0], canvas_w)
        disp_h = resolve_value(disp_size[1], canvas_h)

        # Colors
        border_color: Optional[Tuple[int, ...]] = None
        border_width = config.get("border_width", 3)
        if config.get("border_color"):
            border_color = parse_color(config["border_color"])

        corner_radius = config.get("corner_radius", 16)

        # Crop source region from canvas
        cropped = canvas.crop((src_x0, src_y0, src_x1, src_y1))

        # Resize to display size (zoom effect)
        zoomed = cropped.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

        # Create shape mask
        mask = Image.new("L", (disp_w, disp_h), 0)
        mask_draw = ImageDraw.Draw(mask)

        if shape == "circle":
            mask_draw.ellipse([0, 0, disp_w - 1, disp_h - 1], fill=255)
        elif shape == "rounded_rect":
            mask_draw.rounded_rectangle(
                [0, 0, disp_w - 1, disp_h - 1], radius=corner_radius, fill=255
            )
        else:
            mask_draw.rectangle([0, 0, disp_w - 1, disp_h - 1], fill=255)

        # Apply mask to zoomed image
        masked_zoom = Image.new("RGBA", (disp_w, disp_h), (0, 0, 0, 0))
        masked_zoom.paste(zoomed, (0, 0), mask)

        # Draw border on masked zoom
        if border_color and border_width > 0:
            border_draw = ImageDraw.Draw(masked_zoom)
            outline = border_color
            if shape == "circle":
                border_draw.ellipse(
                    [0, 0, disp_w - 1, disp_h - 1],
                    outline=outline,
                    width=border_width,
                )
            elif shape == "rounded_rect":
                border_draw.rounded_rectangle(
                    [0, 0, disp_w - 1, disp_h - 1],
                    radius=corner_radius,
                    outline=outline,
                    width=border_width,
                )
            else:
                border_draw.rectangle(
                    [0, 0, disp_w - 1, disp_h - 1],
                    outline=outline,
                    width=border_width,
                )

        # Draw connector line if requested
        connector = config.get("connector", False)
        if connector:
            conn_color = parse_color(
                config.get("connector_color") or config.get("border_color", "#007AFF")
            )
            conn_width = config.get("connector_width", 2)

            connector_overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            conn_draw = ImageDraw.Draw(connector_overlay)
            conn_draw.line(
                [(src_cx, src_cy), (disp_cx, disp_cy)],
                fill=conn_color,
                width=conn_width,
            )
            # Composite connector behind zoom bubble
            composited = Image.alpha_composite(canvas, connector_overlay)
            canvas.paste(composited)

        # Place zoom bubble on canvas
        paste_x = disp_cx - disp_w // 2
        paste_y = disp_cy - disp_h // 2

        zoom_overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        zoom_overlay.paste(masked_zoom, (paste_x, paste_y), masked_zoom)

        composited = Image.alpha_composite(canvas, zoom_overlay)
        canvas.paste(composited)

        logger.info(
            f"Rendered {shape} zoom callout: "
            f"source ({src_cx},{src_cy}) {src_w}x{src_h} -> "
            f"display ({disp_cx},{disp_cy}) {disp_w}x{disp_h}"
        )
