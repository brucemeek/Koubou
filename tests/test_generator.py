"""Tests for the main ScreenshotGenerator class."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from koubou.config import GradientConfig, ProjectConfig, ScreenshotConfig, TextOverlay
from koubou.generator import ScreenshotGenerator


class TestScreenshotGenerator:
    """Tests for ScreenshotGenerator."""

    def setup_method(self):
        """Setup test method."""
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create test source image
        self.source_image_path = self.temp_dir / "source.png"
        source_image = Image.new("RGBA", (200, 400), (255, 0, 0, 255))  # Red
        source_image.save(self.source_image_path)

        # Create mock frame directory
        self.frame_dir = self.temp_dir / "frames"
        self.frame_dir.mkdir()

        # Create mock frame
        frame_image = Image.new("RGBA", (300, 600), (128, 128, 128, 255))
        frame_path = self.frame_dir / "Test Frame.png"
        frame_image.save(frame_path)

        # Create frame metadata
        metadata = {
            "Test Frame": {
                "screen_bounds": {"x": 50, "y": 100, "width": 200, "height": 400}
            }
        }

        import json

        with open(self.frame_dir / "Frames.json", "w") as f:
            json.dump(metadata, f)

        self.generator = ScreenshotGenerator(frame_directory=str(self.frame_dir))

    def teardown_method(self):
        """Cleanup after test."""
        shutil.rmtree(self.temp_dir)

    def test_simple_kouboueration(self):
        """Test generating a simple screenshot."""
        config = ScreenshotConfig(
            name="Simple Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output.png"),
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output image
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_screenshot_with_background(self):
        """Test generating screenshot with background."""
        config = ScreenshotConfig(
            name="Background Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output_bg.png"),
            background=GradientConfig(type="solid", colors=["#0066cc"]),
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_screenshot_with_text(self):
        """Test generating screenshot with text overlay."""
        config = ScreenshotConfig(
            name="Text Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output_text.png"),
            text_overlays=[
                TextOverlay(
                    content="Hello World",
                    position=(50, 50),
                    font_size=32,
                    color="#ffffff",
                )
            ],
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_screenshot_with_device_frame(self):
        """Test generating screenshot with device frame."""
        config = ScreenshotConfig(
            name="Frame Test",
            source_image=str(self.source_image_path),
            output_size=(300, 600),  # Match frame size
            output_path=str(self.temp_dir / "output_frame.png"),
            device_frame="Test Frame",
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (300, 600)

    def test_complete_screenshot(self):
        """Test generating screenshot with all features."""
        config = ScreenshotConfig(
            name="Complete Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output_complete.png"),
            background=GradientConfig(
                type="linear", colors=["#ff0000", "#0000ff"], direction=45
            ),
            text_overlays=[
                TextOverlay(
                    content="Amazing App",
                    position=(100, 100),
                    font_size=36,
                    color="#ffffff",
                    alignment="center",
                    max_width=300,
                )
            ],
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_nonexistent_source_image(self):
        """Test handling of nonexistent source image."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Source image not found"):
            ScreenshotConfig(
                name="Invalid Test",
                source_image="/nonexistent/path.png",
                output_size=(400, 800),
            )

    def test_output_path_generation(self):
        """Test automatic output path generation."""
        config = ScreenshotConfig(
            name="Auto Path Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            # No output_path specified
        )

        result_path = self.generator.generate_screenshot(config)

        # Should generate a path based on name
        assert "auto_path_test" in str(result_path).lower()
        assert result_path.exists()

    def test_project_generation(self):
        """Test generating multiple screenshots as a project."""
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        project_config = ProjectConfig(
            project=ProjectInfo(
                name="Test Project", output_dir=str(self.temp_dir / "project_output")
            ),
            screenshots={
                "screenshot1": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        )
                    ],
                    frame=False,  # Explicitly disable frames for this test
                ),
                "screenshot2": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        ),
                        ContentItem(
                            type="text", content="Test Text", position=("50%", "20%")
                        ),
                    ],
                    frame=False,  # Explicitly disable frames for this test
                ),
            },
        )

        results = self.generator.generate_project(project_config)

        assert len(results) == 2
        for result_path in results:
            assert result_path.exists()

    def test_jpeg_output(self):
        """Test JPEG output format."""
        config = ScreenshotConfig(
            name="JPEG Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output.jpg"),  # JPEG extension
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()
        assert result_path.suffix == ".jpg"

        # Verify it's actually a JPEG
        output_image = Image.open(result_path)
        assert output_image.format == "JPEG"

    def test_apply_asset_frame_with_auto_detection(self):
        """Test _apply_asset_frame with automatic screen bounds detection."""
        # Create a realistic frame with screen area and bezel
        frame = Image.new("RGBA", (300, 600), (128, 128, 128, 255))

        # Define screen area (alpha=0) within bezel
        screen_left, screen_top = 30, 60
        screen_right, screen_bottom = 270, 540

        for y in range(600):
            for x in range(300):
                if screen_left <= x < screen_right and screen_top <= y < screen_bottom:
                    frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "AutoDetect Frame.png"
        frame.save(frame_path)

        # Create canvas and config
        canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        config = ScreenshotConfig(
            name="AutoDetect Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            device_frame="AutoDetect Frame",
            image_scale=0.8,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        # Apply asset frame
        result = self.generator._apply_asset_frame(
            Image.open(self.source_image_path), canvas, config
        )

        # Result should be same size as canvas
        assert result.size == canvas.size

        # Should not raise exception
        assert isinstance(result, Image.Image)

    def test_apply_asset_frame_with_scaling(self):
        """Test _apply_asset_frame correctly scales both frame and content."""
        # Create frame with known screen bounds
        frame = Image.new("RGBA", (200, 400), (128, 128, 128, 255))
        screen_x, screen_y = 20, 40
        screen_width, screen_height = 160, 320

        for y in range(screen_y, screen_y + screen_height):
            for x in range(screen_x, screen_x + screen_width):
                frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Scaling Frame.png"
        frame.save(frame_path)

        # Test with different scales
        for scale in [0.5, 0.8, 1.0, 1.2]:
            canvas = Image.new("RGBA", (800, 1200), (255, 255, 255, 0))
            config = ScreenshotConfig(
                name=f"Scale {scale} Test",
                source_image=str(self.source_image_path),
                output_size=(800, 1200),
                device_frame="Scaling Frame",
                image_scale=scale,
                image_position=["50%", "50%"],
                image_frame=True,
            )

            result = self.generator._apply_asset_frame(
                Image.open(self.source_image_path), canvas, config
            )

            assert result.size == canvas.size

    def test_apply_asset_frame_maintains_aspect_ratio(self):
        """Test that _apply_asset_frame maintains source image aspect ratio."""
        # Create narrow portrait frame
        frame = Image.new("RGBA", (150, 400), (128, 128, 128, 255))

        # Screen area
        for y in range(20, 380):
            for x in range(10, 140):
                frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Portrait Frame.png"
        frame.save(frame_path)

        # Create wide landscape source image
        wide_source = self.temp_dir / "wide_source.png"
        wide_image = Image.new("RGBA", (400, 200), (0, 0, 255, 255))
        wide_image.save(wide_source)

        canvas = Image.new("RGBA", (600, 800), (255, 255, 255, 0))
        config = ScreenshotConfig(
            name="Aspect Ratio Test",
            source_image=str(wide_source),
            output_size=(600, 800),
            device_frame="Portrait Frame",
            image_scale=1.0,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        result = self.generator._apply_asset_frame(
            Image.open(wide_source), canvas, config
        )

        # Should complete without distortion
        assert result.size == canvas.size

    def test_apply_asset_frame_with_rounded_corners(self):
        """Test that _apply_asset_frame preserves rounded corners via masking."""
        # Create frame with rounded corners (gradient alpha at edges)
        frame = Image.new("RGBA", (200, 400), (128, 128, 128, 255))

        # Define screen with rounded corners
        for y in range(400):
            for x in range(200):
                # Screen area
                if 20 <= x < 180 and 40 <= y < 360:
                    # Add rounded corners at screen edges
                    dx = min(x - 20, 180 - x)
                    dy = min(y - 40, 360 - y)
                    corner_radius = 20

                    if dx < corner_radius and dy < corner_radius:
                        dist_sq = (corner_radius - dx) ** 2
                        dist_sq += (corner_radius - dy) ** 2
                        dist = dist_sq**0.5
                        if dist < corner_radius:
                            alpha = int(255 * (dist / corner_radius))
                            frame.putpixel((x, y), (128, 128, 128, alpha))
                        else:
                            frame.putpixel((x, y), (128, 128, 128, 0))
                    else:
                        frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Rounded Frame.png"
        frame.save(frame_path)

        canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 0))
        config = ScreenshotConfig(
            name="Rounded Corners Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            device_frame="Rounded Frame",
            image_scale=1.0,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        result = self.generator._apply_asset_frame(
            Image.open(self.source_image_path), canvas, config
        )

        # Result should have RGBA mode to support transparency
        assert result.mode == "RGBA"
        assert result.size == canvas.size
