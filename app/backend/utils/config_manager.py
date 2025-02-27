import configparser
import os

# Default path for the config file
DEFAULT_CONFIG_PATH = "config/TKDiscRipper.conf"

def get_config(config_file=DEFAULT_CONFIG_PATH):
    """
    Reads and returns the configuration from the given file.
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    # Create a ConfigParser object and read the configuration file
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def set_config(config_file=DEFAULT_CONFIG_PATH, section=None, option=None, value=None):
    """
    Writes/Updates a specific option in the config file.
    """
    config = get_config(config_file)  # Get the current config
    if section not in config:
        config.add_section(section)  # Add the section if it doesn't exist
    
    # Update the option value
    config.set(section, option, value)
    
    # Write the changes back to the config file
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def add_or_update_credentials(config_file=DEFAULT_CONFIG_PATH, username=None, password=None):
    """
    Add or update the credentials in the config file.
    """
    if username and password:
        set_config(config_file, "auth", "username", username)
        set_config(config_file, "auth", "password", password)
    else:
        raise ValueError("Both username and password must be provided to update credentials.")

def remove_section(config_file=DEFAULT_CONFIG_PATH, section=None):
    """
    Remove a section from the config file.
    """
    config = get_config(config_file)
    if section in config:
        config.remove_section(section)
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    else:
        raise ValueError(f"Section '{section}' not found in the config file.")
