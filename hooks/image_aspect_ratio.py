"""Add intrinsic aspect ratios to local content images."""

import html
import logging
import math
import os
import posixpath
import re

from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from PIL import Image, UnidentifiedImageError


log = logging.getLogger("mkdocs.hooks.image_aspect_ratio")

_ASPECT_RATIO_RE = re.compile(r"(?:^|;)\s*aspect-ratio\s*:", re.IGNORECASE)
_SVG_LENGTH_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(?:px)?\s*$"
)


def _svg_length(value):
    """Return an SVG pixel length, ignoring relative or physical units."""

    if value is None:
        return None
    match = _SVG_LENGTH_RE.match(value)
    if match is None:
        return None
    number = float(match.group(1))
    return number if number > 0 else None


@lru_cache(maxsize=256)
def _cached_image_size(path_string, modified_ns, file_size):
    """Read image metadata; stat values form the live-reload cache key."""

    del modified_ns, file_size
    path = Path(path_string)

    if path.suffix.lower() == ".svg":
        root = ElementTree.parse(path).getroot()
        width = _svg_length(root.get("width"))
        height = _svg_length(root.get("height"))
        if width is not None and height is not None:
            return width, height

        view_box = root.get("viewBox")
        if view_box is not None:
            values = view_box.replace(",", " ").split()
            if len(values) == 4:
                width, height = float(values[2]), float(values[3])
                if width > 0 and height > 0:
                    return width, height
        return None

    with Image.open(path) as image:
        width, height = image.size
    if width > 0 and height > 0:
        return float(width), float(height)
    return None


def _image_size(path):
    try:
        stat = path.stat()
        return _cached_image_size(str(path), stat.st_mtime_ns, stat.st_size)
    except (
        OSError,
        UnidentifiedImageError,
        ElementTree.ParseError,
        ValueError,
    ) as error:
        log.debug("Cannot determine dimensions of %s: %s", path, error)
        return None


def _format_number(number):
    if number.is_integer():
        return str(int(number))
    return format(number, ".12g")


def _format_ratio(width, height):
    if width.is_integer() and height.is_integer():
        divisor = math.gcd(int(width), int(height))
        return f"{int(width) // divisor} / {int(height) // divisor}"
    return f"{_format_number(width)} / {_format_number(height)}"


def _local_image_path(src, page, config):
    """Map a rendered relative image URL back into ``docs_dir``."""

    parsed = urlsplit(src)
    if parsed.scheme or parsed.netloc:
        if (
            os.environ.get("DEBUG") == "1"
            and (parsed.scheme in {"http", "https"} or parsed.netloc)
        ):
            log.info(
                "Skipping remote image because its aspect ratio cannot be "
                "determined without downloading it: %s",
                src,
            )
        return None
    if not parsed.path:
        return None

    docs_dir = Path(config.docs_dir).resolve()
    url_path = unquote(parsed.path).replace("\\", "/")
    if url_path.startswith("/"):
        relative_path = posixpath.normpath(url_path.lstrip("/"))
    else:
        page_directory = posixpath.dirname(page.file.url)
        relative_path = posixpath.normpath(
            posixpath.join(page_directory, url_path)
        )

    path = (docs_dir / relative_path).resolve()
    if not path.is_relative_to(docs_dir) or not path.is_file():
        return None
    return path


def _attribute_index(attributes, name):
    return next(
        (
            index
            for index, (attribute_name, _) in enumerate(attributes)
            if attribute_name.lower() == name
        ),
        None,
    )


def _enrich_image_attributes(attributes, intrinsic_size):
    """Add an aspect ratio unless the author already supplied sizing."""

    attributes = list(attributes)
    width, height = intrinsic_size

    width_index = _attribute_index(attributes, "width")
    height_index = _attribute_index(attributes, "height")
    if width_index is not None and height_index is not None:
        return None

    style_index = _attribute_index(attributes, "style")
    style = attributes[style_index][1] if style_index is not None else ""
    style = style or ""
    if _ASPECT_RATIO_RE.search(style):
        return None

    declaration = f"aspect-ratio: {_format_ratio(width, height)}"
    if style_index is None:
        attributes.append(("style", declaration))
    else:
        separator = "" if style.rstrip().endswith(";") else ";"
        attributes[style_index] = (
            attributes[style_index][0],
            f"{style}{separator} {declaration}",
        )
    return attributes


def _serialize_image_tag(attributes, self_closing):
    serialized = []
    for name, value in attributes:
        if value is None:
            serialized.append(name)
        else:
            serialized.append(f'{name}="{html.escape(value, quote=True)}"')
    closing = " />" if self_closing else ">"
    return f"<img {' '.join(serialized)}{closing}"


class _ImageTagParser(HTMLParser):
    """Locate image start tags while leaving all other HTML byte-for-byte."""

    def __init__(self, source, page, config):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.page = page
        self.config = config
        self.cursor = 0
        self.replacements = []

    def _handle_image(self, attributes, self_closing):
        raw_tag = self.get_starttag_text()
        start = self.source.find(raw_tag, self.cursor)
        if start < 0:
            return
        self.cursor = start + len(raw_tag)

        if (
            _attribute_index(attributes, "width") is not None
            and _attribute_index(attributes, "height") is not None
        ):
            return

        src_index = _attribute_index(attributes, "src")
        if src_index is None or attributes[src_index][1] is None:
            return

        path = _local_image_path(
            attributes[src_index][1], self.page, self.config
        )
        if path is None:
            return
        size = _image_size(path)
        if size is None:
            return

        enriched = _enrich_image_attributes(attributes, size)
        if enriched is None:
            return
        replacement = _serialize_image_tag(enriched, self_closing)
        self.replacements.append((start, start + len(raw_tag), replacement))

    def handle_starttag(self, tag, attributes):
        if tag.lower() == "img":
            self._handle_image(attributes, self_closing=False)

    def handle_startendtag(self, tag, attributes):
        if tag.lower() == "img":
            self._handle_image(attributes, self_closing=True)


def on_page_content(html_content, page, config, **kwargs):
    """Enrich local images after MkDocs has resolved their output URLs."""

    parser = _ImageTagParser(html_content, page, config)
    parser.feed(html_content)
    parser.close()

    for start, end, replacement in reversed(parser.replacements):
        html_content = html_content[:start] + replacement + html_content[end:]
    return html_content
