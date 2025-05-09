import configparser
import os
import yaml

DEFAULT_CONFIG_PATH = "config/TKDiscRipper.conf"
DESC_PATH = "config/settings_desc.yaml"

def get_descriptions(desc_file=DESC_PATH):
    if not os.path.exists(desc_file):
        return {}
    with open(desc_file, "r") as f:
        return yaml.safe_load(f) or {}

def get_description(section, key, descs=None):
    descs = descs or get_descriptions()
    return descs.get(section, {}).get(key, "")

def get_config(config_file=DEFAULT_CONFIG_PATH) -> configparser.ConfigParser:
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def set_config(config_file=DEFAULT_CONFIG_PATH, section=None, option=None, value=None):
    config = get_config(config_file)
    if section not in config:
        config.add_section(section)
    config.set(section, option, value)
    with open(config_file, "w") as f:
        config.write(f)

def add_or_update_credentials(config_file=DEFAULT_CONFIG_PATH, username=None, password=None):
    if username and password:
        set_config(config_file, "auth", "username", username)
        set_config(config_file, "auth", "password", password)
    else:
        raise ValueError("Both username and password must be provided")

def remove_section(config_file=DEFAULT_CONFIG_PATH, section=None):
    config = get_config(config_file)
    if section in config:
        config.remove_section(section)
        with open(config_file, "w") as f:
            config.write(f)
