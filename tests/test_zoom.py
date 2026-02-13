"""Tests for the ZoomRenderer."""

from PIL import Image

from koubou.renderers.zoom import ZoomRenderer


class TestZoomRenderer:
    def setup_method(self):
        self.renderer = ZoomRenderer()
        # Canvas with a known color pattern: red square at known position
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        # Draw a red block at (150-250, 350-450) — center of canvas
        for y in range(350, 450):
            for x in range(150, 250):
                self.canvas.putpixel((x, y), (255, 0, 0, 255))

    def test_circle_zoom(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
        }
        self.renderer.render(config, self.canvas)
        # The zoomed area should contain red pixels at the display center
        pixel = self.canvas.getpixel((100, 150))
        assert pixel[0] > 200  # Should have red from the magnified source

    def test_rounded_rect_zoom(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "rounded_rect",
            "border_color": "#007AFF",
            "border_width": 3,
            "corner_radius": 16,
        }
        self.renderer.render(config, self.canvas)
        # Center of display should show magnified red content
        pixel = self.canvas.getpixel((100, 150))
        assert pixel[0] > 200

    def test_zoom_magnification(self):
        """Source content should appear at the display position."""
        config = {
            "source_position": ("200", "400"),
            "source_size": ("50", "50"),
            "display_position": ("300", "100"),
            "display_size": ("100", "100"),
            "shape": "circle",
            "border_color": "#000000",
            "border_width": 2,
        }
        self.renderer.render(config, self.canvas)
        # Display center should show red from source
        pixel = self.canvas.getpixel((300, 100))
        assert pixel[0] > 200

    def test_zoom_with_connector(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("120", "120"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": True,
            "connector_color": "#FF0000",
            "connector_width": 3,
        }
        self.renderer.render(config, self.canvas)
        # Should complete without error
        assert self.canvas.size == (400, 800)

    def test_zoom_connector_default_color(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("120", "120"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": True,
            "connector_width": 2,
        }
        # connector_color not set — should default to border_color
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_zoom_no_connector(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("120", "120"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": False,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_zoom_percentage_positions(self):
        config = {
            "source_position": ("50%", "50%"),
            "source_size": ("25%", "12%"),
            "display_position": ("25%", "20%"),
            "display_size": ("35%", "30%"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_zoom_border_rendering(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#0000FF",
            "border_width": 5,
        }
        self.renderer.render(config, self.canvas)
        # Edge of the circle at display should have blue border
        # Top of display circle: 150 - 75 = 75
        pixel = self.canvas.getpixel((100, 75))
        assert pixel[2] > 150  # Blue channel from border
