import yaml
def read_pipeline(spec: str):
    return yaml.load(spec, Loader=yaml.Loader)
