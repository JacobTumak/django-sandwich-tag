from functools import wraps
from inspect import unwrap, getfullargspec
from typing import TypeAlias

from django import template
from django.template import Template, Context
from django.template.loader import get_template
from django.template.base import FilterExpression, Parser, Token
from django.template.library import Library, parse_bits, TagHelperNode

register = Library()

TemplateSpec: TypeAlias = FilterExpression

def resolve_template_spec(template_spec: TemplateSpec, context: Context) -> Template:
    template_spec = template_spec.resolve(context)
    match template_spec:
        case str():
            if '{{' in template_spec or '{%' in template_spec:
                return Template(template_spec, engine=context.template.engine)
            return context.template.engine.get_template(template_spec).template
        case Template():
            return template_spec
        case _:
            raise template.TemplateSyntaxError(
                f"template param must be a string or a Template object, got {template_spec} instead."
            )


def make_sandwich_tag(
        func=None,
        template: str = None,
        name: str = None,
        takes_context=False,
        child_var_name='sandwich_fixings'
):
    assert template is not None, "Custom sandwich tags require a template"
    template = get_template(template)
    (
        params,
        varargs,
        varkw,
        defaults,
        kwonly,
        kwonly_defaults,
        _,
    ) = getfullargspec(unwrap(func))
    function_name = name or func.__name__

    def compile_func(parser, token):
        nonlocal params, varargs, varkw, defaults, kwonly

        open_sw_tag, *bits = token.split_contents()
        close_sw_tag = "end" + open_sw_tag
        child_nodelist = parser.parse(parse_until=(close_sw_tag,))
        parser.delete_first_token()

        token_args, token_kwargs = parse_bits(
            parser=parser,
            bits=bits,
            params=params,
            varargs=varargs,
            varkw=varkw,
            defaults=defaults,
            kwonly=kwonly,
            kwonly_defaults=kwonly_defaults,
            takes_context=False,
            name=open_sw_tag,
        )
        return SandwichTagNode(func, child_nodelist, template, token_args, token_kwargs, child_var_name)
    compile_func.__name__ = "Compile"+function_name
    return compile_func


def register_sandwich_tag(
        func=None,
        template: str=None,
        name: str=None,
        registry: Library=None,
        takes_context=False,
        child_var_name='sandwich_fixings'
):
    template = get_template(template)
    def dec(func):
        (
            params,
            varargs,
            varkw,
            defaults,
            kwonly,
            kwonly_defaults,
            _,
        ) = getfullargspec(unwrap(func))

        function_name = name or func.__name__

        @wraps(func)
        def compile_func(parser, token):
            nonlocal params, varargs, varkw, defaults, kwonly

            open_sw_tag, *bits = token.split_contents()
            close_sw_tag = "end" + open_sw_tag
            child_nodelist = parser.parse(parse_until=(close_sw_tag,))
            parser.delete_first_token()

            token_args, token_kwargs = parse_bits(
                parser=parser,
                bits=bits,
                params=params,
                varargs=varargs,
                varkw=varkw,
                defaults=defaults,
                kwonly=kwonly,
                kwonly_defaults=kwonly_defaults,
                takes_context=False,
                name=open_sw_tag,
            )
            return SandwichTagNode(func, child_nodelist, template, token_args, token_kwargs, child_var_name)
        registry.tag(function_name, compile_func)
        return func

    if func is None:
        # @register.simple_tag(...)
        return dec
    elif callable(func):
        # @register.simple_tag
        return dec(func)
    else:
        raise ValueError("Invalid arguments provided to register_sandwich_tag")





def add_sandwich_tag_dec(registry: Library):
    def sandwich_tag(
            template,
            func=None,
            name: str = None,
            takes_context=False,
            child_var_name='sandwich_fixings'
    ):
        nonlocal registry
        template = get_template(template)

        def dec(func):
            (
                params,
                varargs,
                varkw,
                defaults,
                kwonly,
                kwonly_defaults,
                _,
            ) = getfullargspec(unwrap(func))

            function_name = name or func.__name__

            @wraps(func)
            def compile_func(parser, token):
                nonlocal params, varargs, varkw, defaults, kwonly

                open_sw_tag, *bits = token.split_contents()
                close_sw_tag = "end" + open_sw_tag
                child_nodelist = parser.parse(parse_until=(close_sw_tag,))
                parser.delete_first_token()

                token_args, token_kwargs = parse_bits(
                    parser=parser,
                    bits=bits,
                    params=params,
                    varargs=varargs,
                    varkw=varkw,
                    defaults=defaults,
                    kwonly=kwonly,
                    kwonly_defaults=kwonly_defaults,
                    takes_context=False,
                    name=open_sw_tag,
                )
                return SandwichTagNode(func, child_nodelist, template, token_args, token_kwargs, child_var_name)

            registry.tag(function_name, compile_func)
            return func

        if func is None:
            # @register.simple_tag(...)
            return dec
        elif callable(func):
            # @register.simple_tag
            return dec(func)
        else:
            raise ValueError("Invalid arguments provided to register_sandwich_tag")
    registry.sandwich_tag = sandwich_tag
    return registry







# the wrapped function returns the context to render a sandwich tag
class SandwichTagNode(TagHelperNode):
    def __init__(self, func, child_nodelist, template, args, kwargs, child_var_name):
        super().__init__(func, False, args, kwargs)
        self.child_nodelist = child_nodelist
        self.template = template
        self.child_var_name = child_var_name

    def render(self, context: Context):
        # parent context is any kwargs passed to the sandwich tag, excluding `template` (see `do_sandwich`)
        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
        bread_context = self.func(*resolved_args, **resolved_kwargs)
        bread_context[self.child_var_name] = self.child_nodelist.render(context)
        return self.template.render(bread_context)


if __name__ == "__main__":
    from django.conf import settings
    from django.apps import apps
    from django.template.loader import get_template
    from sandwich_tag.templatetags.demo_new import trial_tag
    apps.apps_ready = True
    trial_tag("Hello", 'some-url', 'some-arg', name="bob")

    print(get_template('bread_demo.html').render({}))

    # apps.apps_ready = True
        # import os
        # from django import setup
        # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
        # setup()
