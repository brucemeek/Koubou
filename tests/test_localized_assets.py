"""Integration tests for localized asset support."""

import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from koubou.config import (
    ContentItem,
    LocalizationConfig,
    ProjectConfig,
    ProjectInfo,
    ScreenshotDefinition,
)
from koubou.generator import ScreenshotGenerator


class TestLocalizedAssets:
    """Integration tests for localized asset resolution."""

    def setup_method(self):
        """Setup test method with localized asset structure."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "output"

        # Create localized directory structure
        # assets/
        #   en/
        #     hero.png (red)
        #     feature.png (blue)
        #   es/
        #     hero.png (green)
        #   hero.png (fallback - yellow)
        self.assets_dir = self.temp_dir / "assets"
        self.assets_dir.mkdir()

        # Create English versions
        en_dir = self.assets_dir / "en"
        en_dir.mkdir()
        Image.new("RGB", (200, 400), (255, 0, 0)).save(en_dir / "hero.png")  # Red
        Image.new("RGB", (200, 400), (0, 0, 255)).save(en_dir / "feature.png")  # Blue

        # Create Spanish versions
        es_dir = self.assets_dir / "es"
        es_dir.mkdir()
        Image.new("RGB", (200, 400), (0, 255, 0)).save(es_dir / "hero.png")  # Green

        # Create fallback version
        Image.new("RGB", (200, 400), (255, 255, 0)).save(
            self.assets_dir / "hero.png"
        )  # Yellow

        # Create explicit mapping assets
        explicit_dir = self.temp_dir / "explicit"
        explicit_dir.mkdir()
        Image.new("RGB", (200, 400), (128, 0, 128)).save(
            explicit_dir / "en_custom.png"
        )  # Purple
        Image.new("RGB", (200, 400), (0, 128, 128)).save(
            explicit_dir / "es_custom.png"
        )  # Cyan
        Image.new("RGB", (200, 400), (128, 128, 128)).save(
            explicit_dir / "fallback.png"
        )  # Gray

        # Create xcstrings with translations
        self.xcstrings_path = self.temp_dir / "Localizable.xcstrings"
        xcstrings_data = {
            "sourceLanguage": "en",
            "strings": {
                "Title Text": {
                    "localizations": {
                        "en": {
                            "stringUnit": {"state": "translated", "value": "Title Text"}
                        },
                        "es": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "Texto del Título",
                            }
                        },
                    }
                }
            },
            "version": "1.0",
        }

        with open(self.xcstrings_path, "w", encoding="utf-8") as f:
            json.dump(xcstrings_data, f, indent=2, ensure_ascii=False)

        self.generator = ScreenshotGenerator()

    def teardown_method(self):
        """Cleanup after test."""
        shutil.rmtree(self.temp_dir)

    def test_convention_based_localized_assets(self):
        """Test convention-based asset resolution with {lang}/ directory pattern."""
        # Create project with localization and convention-based assets
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 - Black - Portrait"],
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset="assets/hero.png",  # Convention-based
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        # Generate screenshots
        results = self.generator.generate_project(project_config, self.temp_dir)

        # Verify both languages generated
        assert len(results) == 2

        # Verify English output exists and uses en/hero.png (red)
        en_output = self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "hero.png"
        assert en_output.exists()
        en_image = Image.open(en_output)
        # Red hero.png should be used
        assert en_image.size[0] > 0

        # Verify Spanish output exists and uses es/hero.png (green)
        es_output = self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "hero.png"
        assert es_output.exists()
        es_image = Image.open(es_output)
        assert es_image.size[0] > 0

    def test_explicit_dict_based_assets(self):
        """Test explicit dict-based asset mapping with per-language paths."""
        # Create project with explicit asset mapping
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 - Black - Portrait"],
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "custom": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset={
                                "en": "explicit/en_custom.png",
                                "es": "explicit/es_custom.png",
                                "default": "explicit/fallback.png",
                            },
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        # Generate screenshots
        results = self.generator.generate_project(project_config, self.temp_dir)

        # Verify both languages generated
        assert len(results) == 2

        # Verify English output uses en_custom.png
        en_output = self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "custom.png"
        assert en_output.exists()

        # Verify Spanish output uses es_custom.png
        es_output = self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "custom.png"
        assert es_output.exists()

    def test_fallback_to_base_language(self):
        """Test fallback to base language when specific language asset not found."""
        # Create project with French language (not available, should fall back to en)
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 - Black - Portrait"],
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "fr"],  # fr assets don't exist
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset="assets/hero.png",
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        # Generate screenshots
        results = self.generator.generate_project(project_config, self.temp_dir)

        # Verify both languages generated (fr falls back to en)
        assert len(results) == 2

        # Verify French output exists and uses en/hero.png as fallback
        fr_output = self.output_dir / "fr" / "iPhone_15_Pro_Portrait" / "hero.png"
        assert fr_output.exists()

    def test_dict_fallback_to_default(self):
        """Test dict format falls back to 'default' when language not found."""
        # Create project with French language using dict with default
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 - Black - Portrait"],
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "fr"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "custom": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset={
                                "en": "explicit/en_custom.png",
                                "es": "explicit/es_custom.png",
                                "default": "explicit/fallback.png",
                            },
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        # Generate screenshots
        results = self.generator.generate_project(project_config, self.temp_dir)

        # Verify both languages generated
        assert len(results) == 2

        # Verify French output exists and uses fallback.png
        fr_output = self.output_dir / "fr" / "iPhone_15_Pro_Portrait" / "custom.png"
        assert fr_output.exists()

    def test_mixed_convention_and_dict_assets(self):
        """Test mixing convention-based and dict-based assets in same screenshot."""
        # Create project with both asset types
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 - Black - Portrait"],
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "mixed": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset="assets/hero.png",  # Convention-based
                            position=("30%", "50%"),
                        ),
                        ContentItem(
                            type="image",
                            asset={  # Dict-based
                                "en": "explicit/en_custom.png",
                                "es": "explicit/es_custom.png",
                            },
                            position=("70%", "50%"),
                        ),
                    ]
                )
            },
        )

        # Generate screenshots
        results = self.generator.generate_project(project_config, self.temp_dir)

        # Verify both languages generated
        assert len(results) == 2

        # Verify outputs exist
        en_output = self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "mixed.png"
        assert en_output.exists()

        es_output = self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "mixed.png"
        assert es_output.exists()

    def test_backward_compatibility_string_assets(self):
        """Test backward compatibility with existing string-based assets."""
        # Create project without localization (single language mode)
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 - Black - Portrait"],
            screenshots={
                "simple": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset="assets/hero.png",  # Direct path
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        # Generate screenshots
        results = self.generator.generate_project(project_config, self.temp_dir)

        # Verify single language generated
        assert len(results) == 1

        # Verify output exists
        output = self.output_dir / "iPhone_15_Pro_Portrait" / "simple.png"
        assert output.exists()
