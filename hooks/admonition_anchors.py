"""Add heading-style permalinks to admonitions with explicit IDs."""

from xml.etree import ElementTree as etree

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import AMP_SUBSTITUTE


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
                for child in title
            ):
                continue

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
    """Register the admonition anchor treeprocessor."""

    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.treeprocessors.register(
            AdmonitionAnchorsTreeprocessor(md), "admonition_anchors", 4
        )


def on_config(config):
    """Add the local Markdown extension after MkDocs loads its configuration."""

    config.markdown_extensions.append(AdmonitionAnchorsExtension())
    return config
