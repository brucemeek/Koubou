"""Tests for the HighlightRenderer."""

from PIL import Image

from koubou.renderers.highlight import HighlightRenderer


class TestHighlightRenderer:
    def setup_method(self):
        self.renderer = HighlightRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))

    def test_circle_highlight(self):
        config = {
            "shape": "circle",
            "position": ("50%", "50%"),
            "dimensions": ("20%", "15%"),
            "border_color": "#FF3B30",
            "border_width": 4,
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((200, 340))
        assert pixel[0] > 200

    def test_rounded_rect_highlight(self):
        config = {
            "shape": "rounded_rect",
            "position": ("50%", "50%"),
            "dimensions": ("40%", "30%"),
            "border_color": "#00FF00",
            "border_width": 4,
            "corner_radius": 16,
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((200, 400))
        assert pixel == (255, 255, 255, 255)

    def test_rect_highlight(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("40%", "30%"),
            "border_color": "#0000FF",
            "border_width": 4,
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((200, 280))
        assert pixel[2] > 200

    def test_highlight_with_fill(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("40%", "30%"),
            "border_color": "#FF0000",
            "border_width": 2,
            "fill_color": "#00FF0080",
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((200, 400))
        assert pixel[1] > pixel[0]

    def test_highlight_border_only_no_fill(self):
        config = {
            "shape": "circle",
            "position": ("200", "400"),
            "dimensions": ("100", "100"),
            "border_color": "#FF0000",
            "border_width": 3,
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((200, 400))
        assert pixel == (255, 255, 255, 255)

    def test_highlight_pixel_positions(self):
        config = {
            "shape": "rect",
            "position": ("100", "200"),
            "dimensions": ("50", "50"),
            "border_color": "#FF0000",
            "border_width": 2,
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((100, 175))
        assert pixel[0] > 200

    def test_highlight_percentage_positions(self):
        config = {
            "shape": "rect",
            "position": ("25%", "25%"),
            "dimensions": ("10%", "10%"),
            "border_color": "#FF0000",
            "border_width": 3,
        }
        self.renderer.render(config, self.canvas)
        pixel = self.canvas.getpixel((100, 160))
        assert pixel[0] > 200

    def test_highlight_large_border_width(self):
        config = {
            "shape": "circle",
            "position": ("50%", "50%"),
            "dimensions": ("30%", "30%"),
            "border_color": "#0000FF",
            "border_width": 10,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)


class TestHighlightShadow:
    def setup_method(self):
        self.renderer = HighlightRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))

    def test_shadow_enabled(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("40%", "30%"),
            "border_color": "#FF0000",
            "border_width": 3,
            "shadow": True,
        }
        self.renderer.render(config, self.canvas)
        # Shadow should darken pixels below the shape
        # Shape bottom edge: cy + h//2 = 400 + 120 = 520
        # Shadow offset default (0,6) + blur should affect pixels below
        pixel = self.canvas.getpixel((200, 540))
        assert pixel != (255, 255, 255, 255)

    def test_shadow_custom_params(self):
        config = {
            "shape": "circle",
            "position": ("50%", "50%"),
            "dimensions": ("30%", "30%"),
            "border_color": "#0000FF",
            "border_width": 3,
            "shadow": True,
            "shadow_color": "#FF000080",
            "shadow_blur": 20,
            "shadow_offset": ("10", "10"),
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_shadow_disabled_no_effect(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("20%", "20%"),
            "border_color": "#FF0000",
            "border_width": 3,
            "shadow": False,
        }
        canvas_before = self.canvas.copy()
        self.renderer.render(config, self.canvas)
        # Compare a pixel far from the shape
        assert self.canvas.getpixel((10, 10)) == canvas_before.getpixel((10, 10))


class TestHighlightSpotlight:
    def setup_method(self):
        self.renderer = HighlightRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))

    def test_spotlight_dims_background(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("40%", "30%"),
            "border_color": "#FF0000",
            "border_width": 3,
            "spotlight": True,
            "spotlight_opacity": 0.5,
        }
        self.renderer.render(config, self.canvas)
        # Corner should be dimmed (not pure white)
        pixel = self.canvas.getpixel((10, 10))
        assert pixel[0] < 255

    def test_spotlight_preserves_highlight_center(self):
        config = {
            "shape": "rect",
            "position": ("200", "400"),
            "dimensions": ("100", "100"),
            "border_color": "#FF0000",
            "border_width": 2,
            "spotlight": True,
            "spotlight_opacity": 0.5,
        }
        self.renderer.render(config, self.canvas)
        # Center of highlight should remain white (not dimmed)
        pixel = self.canvas.getpixel((200, 400))
        assert pixel[0] == 255
        assert pixel[1] == 255
        assert pixel[2] == 255

    def test_spotlight_custom_color(self):
        config = {
            "shape": "circle",
            "position": ("50%", "50%"),
            "dimensions": ("30%", "30%"),
            "border_color": "#FF0000",
            "border_width": 3,
            "spotlight": True,
            "spotlight_color": "#0000FF",
            "spotlight_opacity": 0.5,
        }
        self.renderer.render(config, self.canvas)
        # Corner should have blue tint
        pixel = self.canvas.getpixel((10, 10))
        assert pixel[2] > pixel[0]


class TestHighlightBlurBackground:
    def setup_method(self):
        self.renderer = HighlightRenderer()
        # Create canvas with a sharp pattern (alternating stripes)
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        for x in range(0, 400, 2):
            for y in range(800):
                self.canvas.putpixel((x, y), (0, 0, 0, 255))

    def test_blur_background_applied(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("40%", "30%"),
            "border_color": "#FF0000",
            "border_width": 3,
            "blur_background": True,
            "blur_radius": 20,
        }
        self.renderer.render(config, self.canvas)
        # Corner should be blurred (grey-ish, not pure black or white)
        pixel = self.canvas.getpixel((10, 10))
        assert 50 < pixel[0] < 200

    def test_blur_preserves_highlight_area(self):
        config = {
            "shape": "rect",
            "position": ("200", "400"),
            "dimensions": ("100", "100"),
            "border_color": "#FF0000",
            "border_width": 2,
            "blur_background": True,
            "blur_radius": 20,
        }
        self.renderer.render(config, self.canvas)
        # Inside highlight, the sharp pattern should remain
        # At x=200 (even), should still be black
        pixel = self.canvas.getpixel((200, 400))
        assert pixel[0] == 0

    def test_blur_disabled(self):
        config = {
            "shape": "rect",
            "position": ("50%", "50%"),
            "dimensions": ("20%", "20%"),
            "border_color": "#FF0000",
            "border_width": 3,
            "blur_background": False,
        }
        self.renderer.render(config, self.canvas)
        # Corner should remain sharp (either 0 or 255)
        pixel = self.canvas.getpixel((10, 10))
        assert pixel[0] == 0 or pixel[0] == 255
