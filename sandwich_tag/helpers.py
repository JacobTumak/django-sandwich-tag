from functools import wraps
from inspect import unwrap, getfullargspec

from django.template import Template
from django.utils.itercompat import is_iterable
from django.template.library import Library, parse_bits, TagHelperNode
from django.template.backends.django import Template as BackendTemplate


DEFAULT_CHILD_VAR_NAME = 'sandwich_fixings'
DEFAULT_TAKES_CONTEXT = False
DEFAULT_BREAD_USES_GLOBAL_CONTEXT = False
DEFAULT_CHILDREN_USE_GLOBAL_CONTEXT = True

def get_compile_func(
        func,
        template: str,
        name: str = None,
        takes_context=DEFAULT_TAKES_CONTEXT,
        bread_uses_global_context=DEFAULT_BREAD_USES_GLOBAL_CONTEXT,
        children_use_global_context=DEFAULT_CHILDREN_USE_GLOBAL_CONTEXT,
        child_var_name=DEFAULT_CHILD_VAR_NAME,
):
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
        assert params[0] == 'context', (
            'First param of custom sandwich tag must be `context` if `takes_context` is `True`'
        )

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
        return SandwichTagNode(
            func=func,
            args=token_args,
            kwargs=token_kwargs,
            filename=template,
            child_nodelist=child_nodelist,
            takes_context=takes_context,
            child_var_name=child_var_name,
            bread_uses_global_context=bread_uses_global_context,
            children_use_global_context=children_use_global_context,
        )

    compile_func.__name__ = function_name
    return compile_func


def register_sandwich_tag(
        template: str,
        registry: Library = None,
        name: str = None,
        func=None,
        takes_context=DEFAULT_TAKES_CONTEXT,
        bread_uses_global_context=DEFAULT_BREAD_USES_GLOBAL_CONTEXT,
        children_use_global_context=DEFAULT_CHILDREN_USE_GLOBAL_CONTEXT,
        child_var_name=DEFAULT_CHILD_VAR_NAME,
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
                bread_uses_global_context=bread_uses_global_context,
                children_use_global_context=children_use_global_context,
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
            name: str = None,
            func=None,
            takes_context=DEFAULT_TAKES_CONTEXT,
            child_var_name=DEFAULT_CHILD_VAR_NAME,
            bread_uses_global_context=DEFAULT_BREAD_USES_GLOBAL_CONTEXT,
            children_use_global_context=DEFAULT_CHILDREN_USE_GLOBAL_CONTEXT,
    ):
        return register_sandwich_tag(
            template=template,
            registry=registry,
            name=name,
            func=func,
            takes_context=takes_context,
            bread_uses_global_context=bread_uses_global_context,
            children_use_global_context=children_use_global_context,
            child_var_name=child_var_name,
        )

    registry.sandwich_tag = sandwich_tag
    return registry


def get_and_set_template_from_spec(spec, context, node):
    t = context.render_context.get(node)
    if t is None:
        if isinstance(spec, (Template, BackendTemplate)):
            t = spec
        elif isinstance(getattr(spec, "template", None), Template):
            t = spec.template
        elif not isinstance(spec, str) and is_iterable(spec):
            t = context.template.engine.select_template(spec)
        else:
            t = context.template.engine.get_template(spec)
        context.render_context[node] = t
    return t


class SandwichTagNode(TagHelperNode):
    def __init__(
            self,
            func,
            args,
            kwargs,
            filename,
            child_nodelist,
            takes_context=DEFAULT_TAKES_CONTEXT,
            bread_uses_global_context=DEFAULT_BREAD_USES_GLOBAL_CONTEXT,
            children_use_global_context=DEFAULT_CHILDREN_USE_GLOBAL_CONTEXT,
            child_var_name=DEFAULT_CHILD_VAR_NAME,
    ):
        super().__init__(func, takes_context, args, kwargs)
        self.filename = filename
        self.child_nodelist = child_nodelist
        self.child_var_name = child_var_name
        self.bread_uses_global_context = bread_uses_global_context
        self.children_use_global_context = children_use_global_context

    def render(self, context):
        bread_template = get_and_set_template_from_spec(self.filename, context, self)

        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
        _dict = self.func(*resolved_args, **resolved_kwargs)
        if isinstance(_dict, dict) and self.child_var_name in _dict:
            child_dict = _dict[self.child_var_name]
        else:
            child_dict = {}

        if self.children_use_global_context:
            with context.push(child_dict):
                rendered_children = self.child_nodelist.render(context)
        else:
            rendered_children = self.child_nodelist.render(context.new(child_dict))

        if self.bread_uses_global_context:
            with context.push(_dict):
                context[self.child_var_name] = rendered_children
                return bread_template.render(context)

        bread_context = context.new(_dict)
        bread_context[self.child_var_name] = rendered_children
        return bread_template.render(bread_context)
