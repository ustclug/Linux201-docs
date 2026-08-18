"""Support IDs and heading-style permalinks on admonitions."""

import re

from xml.etree import ElementTree as etree

from markdown.extensions import Extension
from markdown.extensions.admonition import AdmonitionProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.util import AMP_SUBSTITUTE
from pymdownx.details import DetailsProcessor


_ID_PATTERN = r"[^{}\s]+"


class AdmonitionIdProcessor(AdmonitionProcessor):
    """Add an optional ``{#id}`` suffix to traditional admonitions."""

    RE = re.compile(
        rf'(?:^|\n)!!! ?([\w\-]+(?: +[\w\-]+)*)(?: +"(.*?)")?'
        rf'(?: +\{{#({_ID_PATTERN})\}})? *(?:\n|$)'
    )

    def run(self, parent, blocks):
        match = self.RE.search(blocks[0])
        anchor_id = match.group(3) if match else None

        super().run(parent, blocks)

        if anchor_id is not None:
            parent[-1].set("id", anchor_id)


class DetailsIdProcessor(DetailsProcessor):
    """Add an optional ``{#id}`` suffix to traditional details blocks."""

    START = re.compile(
        rf'(?:^|\n)\?{{3}}(\+)? ?(?:([\w\-]+(?: +[\w\-]+)*?)?'
        rf'(?: +"(.*?)")|([\w\-]+(?: +[\w\-]+)*?))'
        rf'(?: +\{{#({_ID_PATTERN})\}})? *(?:\n|$)'
    )

    def run(self, parent, blocks):
        match = self.START.search(blocks[0])
        anchor_id = match.group(5) if match else None

        super().run(parent, blocks)

        if anchor_id is not None:
            parent[-1].set("id", anchor_id)


class AdmonitionAnchorsTreeprocessor(Treeprocessor):
    """Append permalinks to titled admonition containers with IDs."""

    def run(self, root):
        for block in root.iter():
            anchor_id = block.get("id")
            if not anchor_id:
                continue

            classes = set(block.get("class", "").split())
            if block.tag == "div" and "admonition" in classes:
                title = next(
                    (
                        child
                        for child in block
                        if child.tag == "p"
                        and "admonition-title"
                        in child.get("class", "").split()
                    ),
                    None,
                )
            elif block.tag == "details":
                title = next(
                    (child for child in block if child.tag == "summary"), None
                )
            else:
                continue

            if title is None or any(
                child.tag == "a"
                and "headerlink" in child.get("class", "").split()
                for child in title.iter()
            ):
                continue

            word_joiner = f"{AMP_SUBSTITUTE}#8288;"
            if len(title):
                last = title[-1]
                last.tail = f"{last.tail or ''}{word_joiner}"
            else:
                title.text = f"{title.text or ''}{word_joiner}"

            permalink = etree.SubElement(
                title,
                "a",
                {
                    "class": "headerlink",
                    "href": f"#{anchor_id}",
                    "title": "Permanent link",
                },
            )
            permalink.text = f"{AMP_SUBSTITUTE}para;"

        return root


class AdmonitionAnchorsExtension(Extension):
    """Register traditional ID support and the anchor treeprocessor."""

    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.parser.blockprocessors.register(
            AdmonitionIdProcessor(md.parser), "admonition", 105
        )
        md.parser.blockprocessors.register(
            DetailsIdProcessor(md.parser), "details", 105
        )
        md.treeprocessors.register(
            AdmonitionAnchorsTreeprocessor(md), "admonition_anchors", 4
        )


def on_config(config):
    """Add the local Markdown extension after MkDocs loads its configuration."""

    config.markdown_extensions.append(AdmonitionAnchorsExtension())
    return config
