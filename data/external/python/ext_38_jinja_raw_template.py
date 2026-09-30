from jinja2 import Template
def render_profile(template_str: str, ctx: dict) -> str:
    return Template(template_str).render(**ctx)
