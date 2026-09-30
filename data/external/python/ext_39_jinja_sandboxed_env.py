from jinja2.sandbox import SandboxedEnvironment
def render_safe_profile(template_str: str, ctx: dict) -> str:
    env = SandboxedEnvironment()
    return env.from_string(template_str).render(**ctx)
