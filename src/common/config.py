from dynaconf import Dynaconf

config = Dynaconf(
    envvar_prefix='',
    settings_files=['config.json'],
    enviorments=True
)
