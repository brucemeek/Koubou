"""Zoom callout renderer for screenshots."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from ..exceptions import ZoomRenderError
from .utils import (
    compute_bezier_points,
    compute_facing_connector_points,
    draw_shadow,
    draw_shape_mask_aa,
    parse_color,
    resolve_value,
)

logger = logging.getLogger(__name__)

AA_SCALE = 2


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

        # Handle zoom_level shorthand
        zoom_level = config.get("zoom_level")
        if zoom_level is not None and config.get("display_size") is None:
            disp_w = int(src_w * zoom_level)
            disp_h = int(src_h * zoom_level)
        else:
            disp_size = config["display_size"]
            disp_w = resolve_value(disp_size[0], canvas_w)
            disp_h = resolve_value(disp_size[1], canvas_h)

        # Resolve display position
        disp_pos = config.get("display_position", ("25%", "25%"))
        disp_cx = resolve_value(disp_pos[0], canvas_w)
        disp_cy = resolve_value(disp_pos[1], canvas_h)

        # Colors
        border_color: Optional[Tuple[int, ...]] = None
        border_width = config.get("border_width", 3)
        if config.get("border_color"):
            border_color = parse_color(config["border_color"])

        corner_radius = config.get("corner_radius", 16)

        # Source and display bounding boxes
        src_bbox = (src_x0, src_y0, src_x1, src_y1)
        disp_x0 = disp_cx - disp_w // 2
        disp_y0 = disp_cy - disp_h // 2
        disp_x1 = disp_cx + disp_w // 2
        disp_y1 = disp_cy + disp_h // 2
        disp_bbox = (disp_x0, disp_y0, disp_x1, disp_y1)

        # Source region indicator
        source_indicator = config.get("source_indicator", True)
        if source_indicator and border_color:
            self._render_source_indicator(
                config, canvas, src_bbox, border_color, border_width, corner_radius
            )

        # Draw connector line if requested (behind zoom bubble)
        connector = config.get("connector", False)
        if connector:
            self._render_connector(
                config,
                canvas,
                src_bbox,
                disp_bbox,
                src_cx,
                src_cy,
                disp_cx,
                disp_cy,
            )

        # Crop source region from canvas
        cropped = canvas.crop((src_x0, src_y0, src_x1, src_y1))

        # Resize to display size (zoom effect)
        zoomed = cropped.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

        # Create anti-aliased shape mask
        mask = draw_shape_mask_aa((disp_w, disp_h), shape, corner_radius=corner_radius)

        # Apply mask to zoomed image
        masked_zoom = Image.new("RGBA", (disp_w, disp_h), (0, 0, 0, 0))
        masked_zoom.paste(zoomed, (0, 0), mask)

        # Draw border on masked zoom using supersampled rendering
        if border_color and border_width > 0:
            border_layer = Image.new(
                "RGBA", (disp_w * AA_SCALE, disp_h * AA_SCALE), (0, 0, 0, 0)
            )
            bd = ImageDraw.Draw(border_layer)
            scaled_bw = border_width * AA_SCALE
            scaled_cr = corner_radius * AA_SCALE
            scaled_box = [0, 0, disp_w * AA_SCALE - 1, disp_h * AA_SCALE - 1]

            if shape == "circle":
                bd.ellipse(scaled_box, outline=border_color, width=scaled_bw)
            elif shape == "rounded_rect":
                bd.rounded_rectangle(
                    scaled_box, radius=scaled_cr, outline=border_color, width=scaled_bw
                )
            else:
                bd.rectangle(scaled_box, outline=border_color, width=scaled_bw)

            border_layer = border_layer.resize(
                (disp_w, disp_h), Image.Resampling.LANCZOS
            )
            masked_zoom = Image.alpha_composite(masked_zoom, border_layer)

        # Drop shadow on zoom bubble
        if config.get("shadow"):
            shadow_color = config.get("shadow_color", "#00000040")
            shadow_blur_val = config.get("shadow_blur", 15)
            offset = config.get("shadow_offset", ("0", "6"))
            shadow_offset = (int(offset[0]), int(offset[1]))

            shadow_layer = draw_shadow(
                canvas.size,
                shape,
                disp_bbox,
                shadow_color=shadow_color,
                shadow_blur=shadow_blur_val,
                shadow_offset=shadow_offset,
                corner_radius=corner_radius,
            )
            composited = Image.alpha_composite(canvas, shadow_layer)
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

    def _render_source_indicator(
        self,
        config: dict,
        canvas: Image.Image,
        src_bbox: Tuple[int, int, int, int],
        border_color: Tuple[int, ...],
        border_width: int,
        corner_radius: int,
    ) -> None:
        """Draw an outline on the source region to show where the zoom came from."""
        style = config.get("source_indicator_style", "border")
        shape = config.get("shape", "circle")
        x0, y0, x1, y1 = src_bbox

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if style == "fill":
            fill = (
                *border_color[:3],
                min(border_color[3] if len(border_color) > 3 else 255, 40),
            )
            if shape == "circle":
                draw.ellipse(
                    [x0, y0, x1, y1],
                    fill=fill,
                    outline=border_color,
                    width=border_width,
                )
            elif shape == "rounded_rect":
                draw.rounded_rectangle(
                    [x0, y0, x1, y1],
                    radius=corner_radius,
                    fill=fill,
                    outline=border_color,
                    width=border_width,
                )
            else:
                draw.rectangle(
                    [x0, y0, x1, y1],
                    fill=fill,
                    outline=border_color,
                    width=border_width,
                )
        elif style == "dashed":
            self._draw_dashed_rect(
                draw, src_bbox, border_color, border_width, dash_length=10
            )
        else:
            # Default "border" style
            if shape == "circle":
                draw.ellipse([x0, y0, x1, y1], outline=border_color, width=border_width)
            elif shape == "rounded_rect":
                draw.rounded_rectangle(
                    [x0, y0, x1, y1],
                    radius=corner_radius,
                    outline=border_color,
                    width=border_width,
                )
            else:
                draw.rectangle(
                    [x0, y0, x1, y1], outline=border_color, width=border_width
                )

        composited = Image.alpha_composite(canvas, overlay)
        canvas.paste(composited)

    def _draw_dashed_rect(
        self,
        draw: ImageDraw.ImageDraw,
        bbox: Tuple[int, int, int, int],
        color: Tuple[int, ...],
        width: int,
        dash_length: int = 10,
    ) -> None:
        """Draw a dashed rectangle."""
        x0, y0, x1, y1 = bbox
        gap = dash_length

        # Top edge
        x = x0
        while x < x1:
            end = min(x + dash_length, x1)
            draw.line([(x, y0), (end, y0)], fill=color, width=width)
            x += dash_length + gap

        # Right edge
        y = y0
        while y < y1:
            end = min(y + dash_length, y1)
            draw.line([(x1, y), (x1, end)], fill=color, width=width)
            y += dash_length + gap

        # Bottom edge
        x = x0
        while x < x1:
            end = min(x + dash_length, x1)
            draw.line([(x, y1), (end, y1)], fill=color, width=width)
            x += dash_length + gap

        # Left edge
        y = y0
        while y < y1:
            end = min(y + dash_length, y1)
            draw.line([(x0, y), (x0, end)], fill=color, width=width)
            y += dash_length + gap

    def _render_connector(
        self,
        config: dict,
        canvas: Image.Image,
        src_bbox: Tuple[int, int, int, int],
        disp_bbox: Tuple[int, int, int, int],
        src_cx: int,
        src_cy: int,
        disp_cx: int,
        disp_cy: int,
    ) -> None:
        """Draw connector between source and display regions."""
        conn_color = parse_color(
            config.get("connector_color") or config.get("border_color", "#007AFF")
        )
        conn_width = config.get("connector_width", 2)
        style = config.get("connector_style", "straight")

        connector_overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        conn_draw = ImageDraw.Draw(connector_overlay)

        if style == "curved":
            points = compute_bezier_points(
                (src_cx, src_cy), (disp_cx, disp_cy), bow_factor=0.3
            )
            for i in range(len(points) - 1):
                conn_draw.line(
                    [points[i], points[i + 1]], fill=conn_color, width=conn_width
                )

        elif style == "facing":
            sp1, sp2, dp1, dp2 = compute_facing_connector_points(src_bbox, disp_bbox)
            conn_draw.line([sp1, dp1], fill=conn_color, width=conn_width)
            conn_draw.line([sp2, dp2], fill=conn_color, width=conn_width)

            # Optional fill between the two lines
            if config.get("connector_fill"):
                fill_color = parse_color(config["connector_fill"])
                conn_draw.polygon([sp1, sp2, dp2, dp1], fill=fill_color)

        else:
            # Default "straight"
            conn_draw.line(
                [(src_cx, src_cy), (disp_cx, disp_cy)],
                fill=conn_color,
                width=conn_width,
            )

        composited = Image.alpha_composite(canvas, connector_overlay)
        canvas.paste(composited)
