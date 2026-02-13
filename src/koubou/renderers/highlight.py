"""Highlight annotation renderer for screenshots."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageFilter

from ..exceptions import HighlightRenderError
from .utils import (
    draw_shadow,
    draw_shape_aa,
    draw_shape_mask_aa,
    parse_color,
    resolve_value,
)

logger = logging.getLogger(__name__)


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
        bbox = (x0, y0, x1, y1)

        # Spotlight mode: dim everything outside the highlight area
        if config.get("spotlight"):
            self._render_spotlight(config, canvas, shape, bbox, corner_radius)

        # Blur background: blur everything outside the highlight area
        if config.get("blur_background"):
            self._render_blur_background(config, canvas, shape, bbox, corner_radius)

        # Drop shadow
        if config.get("shadow"):
            shadow_color = config.get("shadow_color", "#00000040")
            shadow_blur = config.get("shadow_blur", 15)
            offset = config.get("shadow_offset", ("0", "6"))
            shadow_offset = (int(offset[0]), int(offset[1]))

            shadow_layer = draw_shadow(
                canvas.size,
                shape,
                bbox,
                shadow_color=shadow_color,
                shadow_blur=shadow_blur,
                shadow_offset=shadow_offset,
                corner_radius=corner_radius,
            )
            composited = Image.alpha_composite(canvas, shadow_layer)
            canvas.paste(composited)

        # Draw highlight shape with anti-aliasing
        outline = border_color if border_color else None
        fill = fill_color if fill_color else None
        width = border_width if outline else 0

        overlay = draw_shape_aa(
            canvas.size,
            shape,
            bbox,
            fill=fill,
            outline=outline,
            width=width,
            corner_radius=corner_radius,
        )

        composited = Image.alpha_composite(canvas, overlay)
        canvas.paste(composited)

        logger.info(f"Rendered {shape} highlight at ({cx},{cy}) size {w}x{h}")

    def _render_spotlight(
        self,
        config: dict,
        canvas: Image.Image,
        shape: str,
        bbox: Tuple[int, int, int, int],
        corner_radius: int,
    ) -> None:
        """Dim everything outside the highlight shape."""
        spotlight_color = parse_color(config.get("spotlight_color", "#000000"))
        opacity = config.get("spotlight_opacity", 0.5)
        alpha = int(255 * opacity)

        # Create dark overlay
        overlay = Image.new("RGBA", canvas.size, (*spotlight_color[:3], alpha))

        # Cut out the highlight shape using an anti-aliased mask
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        cutout_mask = draw_shape_mask_aa((w, h), shape, corner_radius=corner_radius)

        # Apply cutout: set overlay alpha to 0 inside the shape
        overlay_alpha = overlay.split()[3]
        overlay_alpha.paste(0, (bbox[0], bbox[1]), cutout_mask)
        overlay.putalpha(overlay_alpha)

        composited = Image.alpha_composite(canvas, overlay)
        canvas.paste(composited)

    def _render_blur_background(
        self,
        config: dict,
        canvas: Image.Image,
        shape: str,
        bbox: Tuple[int, int, int, int],
        corner_radius: int,
    ) -> None:
        """Blur everything outside the highlight shape."""
        blur_radius = config.get("blur_radius", 20)

        blurred = canvas.copy().filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Create mask for the sharp (highlight) area
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        sharp_mask = draw_shape_mask_aa((w, h), shape, corner_radius=corner_radius)

        # Full-canvas mask: 255 = show blurred, 0 = show sharp original
        full_mask = Image.new("L", canvas.size, 255)
        full_mask.paste(0, (bbox[0], bbox[1]), sharp_mask)

        # Composite: blurred where mask is 255, original where 0
        result = Image.composite(blurred, canvas, full_mask)
        canvas.paste(result)
