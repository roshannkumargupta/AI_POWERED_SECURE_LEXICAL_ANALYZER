import yaml
with open('config.yml', encoding='utf-8') as config:
    settings = yaml.load(config)
print(settings)
