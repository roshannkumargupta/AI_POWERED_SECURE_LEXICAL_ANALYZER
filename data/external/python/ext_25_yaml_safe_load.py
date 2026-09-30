import yaml
def read_pipeline_safe(spec: str):
    return yaml.safe_load(spec)
