from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Dream Oracle iOS app icons from the source icon."
    )
    parser.add_argument("--app-root", help="Path to the Dream Oracle repository root")
    parser.add_argument("--source-icon", help="Path to the source icon file")
    parser.add_argument(
        "--app-icon-set",
        help="Path to the iOS AppIcon.appiconset directory",
    )
    return parser.parse_args()


def resolve_app_root(explicit_root: str | None) -> Path:
    repo_root = Path(__file__).resolve().parent

    candidates = []
    if explicit_root:
        candidates.append(Path(explicit_root))

    env_root = __import__("os").environ.get("DREAM_ORACLE_APP_ROOT")
    if env_root:
        candidates.append(Path(env_root))

    candidates.extend(
        [
            repo_root.parent / "Dream_Oracle",
            repo_root.parent / "dream-oracle",
            repo_root.parent / "dream_oracle",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "Dream Oracle repo not found. Pass --app-root or set DREAM_ORACLE_APP_ROOT."
    )


def resolve_source_icon(app_root: Path, explicit_icon: str | None) -> Path:
    if explicit_icon:
        source_icon = Path(explicit_icon)
    else:
        source_icon = app_root / "public" / "icons" / "icon-512x512.webp"

    if not source_icon.exists():
        raise FileNotFoundError(f"Source icon not found: {source_icon}")

    return source_icon.resolve()


def resolve_app_icon_set(app_root: Path, explicit_icon_set: str | None) -> Path:
    if explicit_icon_set:
        app_icon_set = Path(explicit_icon_set)
    else:
        app_icon_set = (
            app_root
            / "apps"
            / "mobile_flutter"
            / "ios"
            / "Runner"
            / "Assets.xcassets"
            / "AppIcon.appiconset"
        )

    if not app_icon_set.exists():
        raise FileNotFoundError(f"App icon set not found: {app_icon_set}")

    return app_icon_set.resolve()


def pixel_size(size_value: str, scale_value: str) -> int:
    base_size = float(size_value.split("x", 1)[0])
    scale = int(scale_value.rstrip("x"))
    return int(round(base_size * scale))


def main() -> None:
    args = parse_args()
    app_root = resolve_app_root(args.app_root)
    source_icon = resolve_source_icon(app_root, args.source_icon)
    app_icon_set = resolve_app_icon_set(app_root, args.app_icon_set)
    contents_file = app_icon_set / "Contents.json"

    with contents_file.open("r", encoding="utf-8") as file:
        contents = json.load(file)

    source = Image.open(source_icon).convert("RGB")
    generated_count = 0

    for image_spec in contents["images"]:
        filename = image_spec.get("filename")
        if not filename:
            continue

        icon_size = pixel_size(image_spec["size"], image_spec["scale"])
        resized = source.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        resized.save(app_icon_set / filename, format="PNG")
        generated_count += 1

    print(f"Generated {generated_count} iOS app icons in {app_icon_set}")


if __name__ == "__main__":
    main()