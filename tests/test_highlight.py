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
        # Border should have been drawn - check center-top of ellipse for red
        # The ellipse top is at cy - h//2 = 400 - 60 = 340
        # With border width 4, pixels around boundary should be colored
        pixel = self.canvas.getpixel((200, 340))
        assert pixel[0] > 200  # Red channel should be strong near border

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
        # Center should still be white (no fill)
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
        # Top edge of rectangle: cy - h//2 = 400 - 120 = 280, at x=200
        pixel = self.canvas.getpixel((200, 280))
        assert pixel[2] > 200  # Blue channel should be strong at border

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
        # Center should have green fill blended with white background
        pixel = self.canvas.getpixel((200, 400))
        assert pixel[1] > pixel[0]  # Green channel should dominate over red

    def test_highlight_border_only_no_fill(self):
        config = {
            "shape": "circle",
            "position": ("200", "400"),
            "dimensions": ("100", "100"),
            "border_color": "#FF0000",
            "border_width": 3,
        }
        self.renderer.render(config, self.canvas)
        # Center should remain white (no fill)
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
        # Top edge at y=175, should have red border
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
        # 25% of 400 = 100, 25% of 800 = 200
        # dimensions: 10% of 400 = 40, 10% of 800 = 80
        self.renderer.render(config, self.canvas)
        # Border at top edge: y = 200 - 40 = 160
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
        # Should complete without error
        assert self.canvas.size == (400, 800)
