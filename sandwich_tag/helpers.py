from functools import wraps
from inspect import unwrap, getfullargspec

from django.template import Context
from django.template.loader import get_template
from django.template.library import Library, parse_bits, TagHelperNode

register = Library()

def get_compile_func(
        func,
        template: str,
        name: str = None,
        takes_context=False,
        child_var_name='sandwich_fixings'
):
    template = get_template(template)
    function_name = name or func.__name__
    (
        params,
        varargs,
        varkw,
        defaults,
        kwonly,
        kwonly_defaults,
        _,
    ) = getfullargspec(unwrap(func))
    if takes_context:
        assert params[0] == 'context', ('First param of custom sandwich tag must be context '
                                        'if `takes_context` is True')

    def compile_func(parser, token):

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
            takes_context=takes_context,
            name=open_sw_tag,
        )
        return SandwichTagNode(func, child_nodelist, template, token_args, token_kwargs, child_var_name, takes_context)
    compile_func.__name__ = function_name
    return compile_func


def register_sandwich_tag(
        template: str,
        registry: Library=None,
        name: str=None,
        func=None,
        takes_context=False,
        child_var_name='sandwich_fixings'
):
    def dec(func):

        @wraps(func)
        def compile_func(parser, token):
            return get_compile_func(
                func=func,
                template=template,
                name=name,
                takes_context=takes_context,
                child_var_name=child_var_name,
            )(parser, token)

        registry.tag(compile_func.__name__, compile_func)
        return func

    if func is None:
        return dec
    elif callable(func):
        return dec(func)
    else:
        raise ValueError("Invalid arguments provided to register_sandwich_tag")


def add_sandwich_tag_dec(registry: Library):
    def sandwich_tag(
        template: str,
        name: str=None,
        func=None,
        takes_context=False,
        child_var_name='sandwich_fixings'
    ):
        return register_sandwich_tag(
            template=template,
            registry=registry,
            name=name,
            func=func,
            takes_context=takes_context,
            child_var_name=child_var_name,
        )
    registry.sandwich_tag = sandwich_tag
    return registry


# the wrapped function returns the context to render a sandwich tag
class SandwichTagNode(TagHelperNode):
    def __init__(self, func, child_nodelist, template, args, kwargs, child_var_name, takes_context):
        super().__init__(func, takes_context, args, kwargs)
        self.child_nodelist = child_nodelist
        self.template = template
        self.child_var_name = child_var_name

    def render(self, context: Context):
        # Note: if `takes_context` is truthy, any changes made to context in `self.func` will only affect `child_nodelist`
        with context.push():
            resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
            bread_context = self.func(*resolved_args, **resolved_kwargs)
            bread_context[self.child_var_name] = self.child_nodelist.render(context)
            return self.template.render(bread_context)
