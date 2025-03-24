from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from django.test import SimpleTestCase
from django.utils.safestring import SafeString


class TestSandwichTag(SimpleTestCase):
    def setUp(self):
        self.default_title = "Why a Penguin should be the next president"
        self.default_fixings = "<p>They dress well, and make everyone happy.</p>"
        self.sw_template_name = "bread.html"

    def _sandwich_with_fixings(
        self,
        bread: str | Template,
        title: str | None = None,
        fixings: str | None = None,
        with_title: bool = True,
        bread_as_var: bool = False,
    ) -> Template:
        bread_template = bread if bread_as_var and bread else f"'{bread}'" if bread else ""
        title = f" title='{self.default_title if title is None else title}'" if with_title else ""
        return Template(
            "{% load sandwich %}"
            "{% sandwich " + bread_template + title + " %}"
            f"{self.default_fixings if fixings is None else fixings}"
            "{% endsandwich %}"
        )

    def test_template_not_provided(self):
        self.assertRaises(
            TemplateSyntaxError,
            self._sandwich_with_fixings,
            bread="",
        )

    def test_with_template_object(self):
        """the template passed to a sandwich tag may be a string or Template instance"""
        rendered = self._sandwich_with_fixings("bread_template", bread_as_var=True, title="", fixings="").render(
            Context({"bread_template": get_template(self.sw_template_name).template})
        )
        self.assertHTMLEqual(rendered, "<h1>default title text</h1><div></div>")

    def test_with_template_name(self):
        with_sandwich = self._sandwich_with_fixings(self.sw_template_name).render(Context({}))
        manual = get_template(self.sw_template_name).template.render(  # not treated as a sandwich
            Context(dict(title=self.default_title, sandwich_fixings=SafeString(self.default_fixings)))
        )
        self.assertHTMLEqual(with_sandwich, manual)

    def test_bad_bread_template_type(self):
        """try passing a non-string/non-Template instance as bread"""
        bad_bread_var = "bad_bread"
        context = Context()
        context[bad_bread_var] = {}  # not a string or Template instance
        template = self._sandwich_with_fixings(bad_bread_var, bread_as_var=True)
        self.assertRaises(TemplateSyntaxError, template.render, context)

    def test_sandwich_context_isolation(self):  # alternate name: test_sandwich_context_behaviour
        """
        Ensure that the...
        - parent template only receives context from kwargs passed to the tag
        - fixings template only receives global context (implicit)
        """
        context = Context()
        context["title"] = "custom title text"
        context["body"] = "custom body text"
        rendered = self._sandwich_with_fixings(
            bread=self.sw_template_name,
            fixings="{{ body|default:'default body text' }}",
            with_title=False,
        ).render(context)
        self.assertNotIn("custom title text", rendered)
        self.assertIn("custom body text", rendered)

    def test_resolved_kwargs_not_cached(self):
        """
        Ensure that kwargs are re-resolved on each call to the tag.

        If resolved kwargs are stored in the instance, then they will be cached and
        will not be resolved again.

        That means that if a sandwich tag is in a for-loop block, each iteration
        would use the same values as the first iteration, where the kwargs were resolved.

        That's not what we want.
        """
        context_dict = {
            "titles": [
                "title1",
                "title2",
                "title3",
            ]
        }
        # expected = "\n".join([f"<h1>{d['my_title']}</h1><div></div>" for d in context_dict['kwargs']])
        expected = "<h1>title1</h1><div></div>" "<h1>title2</h1><div></div>" "<h1>title3</h1><div></div>"
        rendered = Template(
            "{% load sandwich %}"
            "{% for my_title in titles %}"
            "{% sandwich 'bread.html' title=my_title %}" 
            "{% endsandwich %}"
            "{% endfor %}"
        ).render(Context(context_dict))
        self.assertHTMLEqual(rendered, expected)

    def test_sandwich_renders_children(self):
        """
        No imposters allowed. Real sandwiches only.
        """
        rendered = self._sandwich_with_fixings(
            bread=self.sw_template_name,
            fixings="{{ body|default:'default body text' }}",
            title="",
        ).render(Context({}))
        self.assertHTMLEqual(rendered, "<h1>default title text</h1><div>default body text</div>")