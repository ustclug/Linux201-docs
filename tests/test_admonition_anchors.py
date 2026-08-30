import unittest

from markdown import Markdown

from material.extensions.admonition import AdmonitionExtension


class AdmonitionAnchorsTest(unittest.TestCase):
    def render(self, source):
        markdown = Markdown(
            extensions=[
                "admonition",
                "pymdownx.blocks.admonition",
                "pymdownx.blocks.details",
                "pymdownx.details",
                AdmonitionExtension(),
            ]
        )
        return markdown.convert(source)

    def assert_permalink(self, html, anchor_id):
        self.assertIn(f'href="#{anchor_id}"', html)
        self.assertIn('class="headerlink"', html)
        self.assertIn('&#8288;<a class="headerlink"', html)

    def test_admonition_with_title_and_id(self):
        html = self.render(
            '!!! tip "this is title" {#tip-summary}\n\n    body'
        )
        self.assertIn('<div class="admonition tip" id="tip-summary">', html)
        self.assertIn(
            '<p class="admonition-title">this is title&#8288;'
            '<a class="headerlink"',
            html,
        )
        self.assert_permalink(html, "tip-summary")

    def test_chinese_title_uses_word_joiner_before_permalink(self):
        html = self.render('!!! example "一个例子标题" {#example}\n\n    body')
        self.assertIn(
            '<p class="admonition-title">一个例子标题&#8288;'
            '<a class="headerlink"',
            html,
        )

    def test_formatted_title_keeps_markup_with_permalink(self):
        html = self.render(
            "/// tip | title with `code`\n"
            "    attrs: {id: formatted-title}\n\n"
            "body\n"
            "///"
        )
        self.assertIn(
            '<p class="admonition-title">title with '
            '<code>code</code>&#8288;<a class="headerlink"',
            html,
        )

    def test_admonition_default_and_blank_titles_with_id(self):
        default_title = self.render('!!! tip {#tip-default}\n\n    body')
        blank_title = self.render('!!! warning "" {#hidden-title}\n\n    body')
        self.assertIn('id="tip-default"', default_title)
        self.assertIn('<p class="admonition-title">Tip', default_title)
        self.assert_permalink(default_title, "tip-default")
        self.assertIn('id="hidden-title"', blank_title)
        self.assertNotIn('class="admonition-title"', blank_title)
        self.assertNotIn('class="headerlink"', blank_title)

    def test_collapsible_details_with_id(self):
        folded = self.render('??? note "folded" {#folded}\n\n    body')
        expanded = self.render('???+ note "expanded" {#expanded}\n\n    body')
        default_title = self.render('??? note {#default-details}\n\n    body')
        self.assertIn('<details class="note" id="folded">', folded)
        self.assertNotIn('open="open"', folded)
        self.assert_permalink(folded, "folded")
        self.assertIn('id="expanded"', expanded)
        self.assertIn('open="open"', expanded)
        self.assert_permalink(expanded, "expanded")
        self.assertIn('id="default-details"', default_title)
        self.assertIn(
            '<summary>Note&#8288;<a class="headerlink"', default_title
        )
        self.assert_permalink(default_title, "default-details")

    def test_nested_admonition_with_id(self):
        html = self.render(
            "1. item\n\n"
            '    !!! tip "nested" {#nested-tip}\n\n'
            "        body"
        )
        self.assertIn('<div class="admonition tip" id="nested-tip">', html)
        self.assert_permalink(html, "nested-tip")

    def test_traditional_syntax_without_id_is_unchanged(self):
        admonition = self.render('!!! tip "legacy"\n\n    body')
        details = self.render('??? note "legacy folded"\n\n    body')
        self.assertIn('<div class="admonition tip">', admonition)
        self.assertIn('<details class="note">', details)
        self.assertNotIn('class="headerlink"', admonition)
        self.assertNotIn('class="headerlink"', details)

    def test_blocks_syntax_keeps_id_and_permalink_support(self):
        admonition = self.render(
            "/// tip | Block title\n"
            "    attrs: {id: block-tip}\n\n"
            "body\n"
            "///"
        )
        details = self.render(
            "/// details | Folded block\n"
            "    type: note\n"
            "    attrs: {id: block-details}\n\n"
            "body\n"
            "///"
        )
        self.assertIn('id="block-tip"', admonition)
        self.assert_permalink(admonition, "block-tip")
        self.assertIn('id="block-details"', details)
        self.assert_permalink(details, "block-details")

    def test_invalid_id_suffix_is_not_parsed_as_an_admonition(self):
        for declaration in (
            '!!! tip "title" {#bad id}',
            '!!! tip "title" {#id} trailing',
            '??? note "title" {#bad id}',
            '??? note "title" {#id} trailing',
        ):
            with self.subTest(declaration=declaration):
                html = self.render(f"{declaration}\n\n    body")
                self.assertNotIn('class="admonition ', html)
                self.assertNotIn("<details", html)


if __name__ == "__main__":
    unittest.main()
