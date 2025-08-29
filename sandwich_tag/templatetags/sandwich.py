from typing import TypeAlias

from django import template
from django.template import Template, Context
from django.template.base import FilterExpression, Parser, Token
from django.template.library import Library, parse_bits


register = Library()


TemplateSpec: TypeAlias = str | Template


def resolve_template_spec(template_spec: TemplateSpec, context: Context) -> Template:
    match template_spec:
        case str():
            if '{{' in template_spec or '{%' in template_spec:
                return Template(template_spec, engine=context.template.engine)
            return context.template.engine.get_template(template_spec)
        case Template():
            return template_spec
        case _:
            raise template.TemplateSyntaxError(
                f"template param must be a string or a Template object, got {template_spec} instead."
            )


@register.tag(name="sandwich")
def do_sandwich(parser: Parser, token: Token) -> template.Node:  # do_{tag} follows djangos convention
    """
    Processes the `sandwich` template tag, which wraps child content in a parent template.

    The `sandwich` tag allows dynamic rendering of a parent template (specified as a string or
    Template object) with a placeholder (`{{ sandwich_fixings }}`) where the child content
    renders. Keyword arguments passed to the tag define the parent template's context, while
    the child template accesses the global context implicitly.

    Args:
        parser (Parser): The template parser instance.
        token (Token): The parsed token containing the tag name and its arguments.

    Returns:
        SandwichNode: A template node that renders the parent template with the child content.

    Raises:
        TemplateSyntaxError: If the `template` argument is missing, invalid, or specified
        both positionally and as a keyword.
    """

    # first bit is tag name, no need to parse it
    open_sw_tag, *bits = token.split_contents()
    close_sw_tag = "end" + open_sw_tag
    child_nodelist = parser.parse(parse_until=(close_sw_tag,))
    parser.delete_first_token()
    takes_context = False
    if any(context_arg := [bits.pop(i) for i, arg in enumerate(bits) if arg == 'context']):
        assert len(context_arg) == 1, "`context` special arg appeared more than once."
        takes_context = True
    token_args, token_kwargs = parse_bits(
        parser=parser,
        bits=bits,
        params=("template",),  # Note that `params` must be an iterable (not `None`)
        varargs=["context"],  # use None if no varargs (DONT USE `False` since it's checked as `if varargs is None`)
        varkw='kwargs',  # accept token_kwargs that aren't in params (like `def func(**token_kwargs)`)
        defaults=None,
        kwonly=(),  # kwonly must be an iterable, we don't have any
        kwonly_defaults=None,
        takes_context=False,  # if true, first elt of params must be `"context"`
        # Note that `sandwich` does take context implicitly in order for the "fixings" to access it, but currently,
        # the parent template has no access to it
        name=open_sw_tag,
    )
    # `parent_fe` is the FilterExpression instance that "knows" the name of the parent template
    # Note that a string with no variables or filters is stored in a FilterExpression instance by django

    if token_args:  # the only other token_arg allowed is the `template`
        if "template" in token_kwargs:
            raise template.TemplateSyntaxError(
                f"{open_sw_tag} tag received template as both positional and keyword argument. "
                "Please remove one of them."
            )
        bread_spec = token_args[0]
    else:
        bread_spec = token_kwargs.pop("template")
    return SandwichNode(child_nodelist, bread_spec, token_kwargs, takes_context)


class SandwichNode(template.Node):
    """passes rendered tag contents to the bread template as context named sandwich_fixings"""

    child_var_name = "sandwich_fixings"

    def __init__(self, child_nodelist: template.NodeList, filter_expression: FilterExpression, token_kwargs, takes_context: bool):
        self.child_nodelist = child_nodelist
        self.filter_expression = filter_expression
        self.token_kwargs = token_kwargs
        self.takes_context = takes_context

    def _get_bread_template(self, context: Context) -> Template:
        template_spec = self.filter_expression.resolve(context)
        return resolve_template_spec(template_spec, context)

    def _resolve_kwargs(self, context) -> dict:
        return {k: getattr(v, "resolve", lambda c: v)(context) for k, v in self.token_kwargs.items()}

    def render_bread(self, template, context: Context, rendered_fixings, overrides) -> str:
        with context.push(overrides):
            context[self.child_var_name] = rendered_fixings
            return template.render(context)

    def render(self, context: Context):
        _dict = self._resolve_kwargs(context)
        template = self._get_bread_template(context)  # use global context to resolve the name of the template
        rendered_children = self.child_nodelist.render(context)
        if self.takes_context:
            print("Using global context")
            return self.render_bread(template, context, rendered_children, _dict)
        print("Using local context")
        return self.render_bread(template, context.new(), rendered_children, _dict)
