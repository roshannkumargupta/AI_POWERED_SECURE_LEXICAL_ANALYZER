import yaml
stream = "a: 1"
yaml.load(stream, Loader=yaml.SafeLoader)
