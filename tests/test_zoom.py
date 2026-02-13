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
        pixel = self.canvas.getpixel((100, 150))
        assert pixel[0] > 200

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
        pixel = self.canvas.getpixel((100, 150))
        assert pixel[0] > 200

    def test_zoom_magnification(self):
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
        pixel = self.canvas.getpixel((100, 75))
        assert pixel[2] > 150


class TestZoomShadow:
    def setup_method(self):
        self.renderer = ZoomRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        for y in range(350, 450):
            for x in range(150, 250):
                self.canvas.putpixel((x, y), (255, 0, 0, 255))

    def test_shadow_enabled(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "shadow": True,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_shadow_custom_params(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "shadow": True,
            "shadow_color": "#00000080",
            "shadow_blur": 20,
            "shadow_offset": ("5", "10"),
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)


class TestZoomSourceIndicator:
    def setup_method(self):
        self.renderer = ZoomRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        for y in range(350, 450):
            for x in range(150, 250):
                self.canvas.putpixel((x, y), (255, 0, 0, 255))

    def test_source_indicator_default_enabled(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#0000FF",
            "border_width": 4,
        }
        self.renderer.render(config, self.canvas)
        # Source region border should be visible at the edge of source
        # Top of source ellipse: 400 - 50 = 350
        pixel = self.canvas.getpixel((200, 350))
        assert pixel[2] > 100

    def test_source_indicator_disabled(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "rect",
            "border_color": "#0000FF",
            "border_width": 4,
            "source_indicator": False,
        }
        # The source region at (150, 350) is on the red block border
        # Without indicator, no blue should be drawn on the source area
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_source_indicator_dashed_style(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "rect",
            "border_color": "#0000FF",
            "border_width": 3,
            "source_indicator": True,
            "source_indicator_style": "dashed",
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_source_indicator_fill_style(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "shape": "rect",
            "border_color": "#0000FF",
            "border_width": 3,
            "source_indicator": True,
            "source_indicator_style": "fill",
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)


class TestZoomConnectorStyles:
    def setup_method(self):
        self.renderer = ZoomRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        for y in range(350, 450):
            for x in range(150, 250):
                self.canvas.putpixel((x, y), (255, 0, 0, 255))

    def test_straight_connector(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("120", "120"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": True,
            "connector_style": "straight",
            "connector_width": 2,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_curved_connector(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("120", "120"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": True,
            "connector_style": "curved",
            "connector_width": 2,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_facing_connector(self):
        config = {
            "source_position": ("200", "600"),
            "source_size": ("100", "100"),
            "display_position": ("200", "200"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": True,
            "connector_style": "facing",
            "connector_width": 2,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_facing_connector_with_fill(self):
        config = {
            "source_position": ("200", "600"),
            "source_size": ("100", "100"),
            "display_position": ("200", "200"),
            "display_size": ("150", "150"),
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
            "connector": True,
            "connector_style": "facing",
            "connector_width": 2,
            "connector_fill": "#007AFF20",
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_facing_connector_horizontal(self):
        config = {
            "source_position": ("100", "400"),
            "source_size": ("60", "60"),
            "display_position": ("300", "400"),
            "display_size": ("120", "120"),
            "shape": "rect",
            "border_color": "#FF0000",
            "border_width": 3,
            "connector": True,
            "connector_style": "facing",
            "connector_width": 2,
        }
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)


class TestZoomLevel:
    def setup_method(self):
        self.renderer = ZoomRenderer()
        self.canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        for y in range(350, 450):
            for x in range(150, 250):
                self.canvas.putpixel((x, y), (255, 0, 0, 255))

    def test_zoom_level_shorthand(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "zoom_level": 2.0,
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
        }
        self.renderer.render(config, self.canvas)
        # Display should be 200x200 (100 * 2.0)
        pixel = self.canvas.getpixel((100, 150))
        assert pixel[0] > 200

    def test_zoom_level_with_display_size_uses_display_size(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("100", "100"),
            "display_position": ("100", "150"),
            "display_size": ("150", "150"),
            "zoom_level": 3.0,
            "shape": "circle",
            "border_color": "#007AFF",
            "border_width": 3,
        }
        # display_size takes precedence when both are set
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)

    def test_zoom_level_fractional(self):
        config = {
            "source_position": ("200", "400"),
            "source_size": ("80", "80"),
            "display_position": ("100", "150"),
            "zoom_level": 2.5,
            "shape": "rounded_rect",
            "border_color": "#007AFF",
            "border_width": 3,
            "corner_radius": 12,
        }
        # Display should be 200x200 (80 * 2.5)
        self.renderer.render(config, self.canvas)
        assert self.canvas.size == (400, 800)
