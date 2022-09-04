from datetime import datetime
import json
import os
from .log_setup import logger
from .version import VERSION  # load version, other modules can access without extra import


### @package environment
#
# Interactions with the environment variables.
#
from typing import Dict, Optional


def load_env(key: str, default: str, config_dict=None) -> str:
    """!
    Function to load a key from environment or from a config-dict\n
    Handles None-types for not set env-variables by returning the default.\n
    Prefers env-variables with same name over contents read from config-file\n
    Does also replace specified expressions like {PREFIX} with actual content.

    @param key: name of env variable to load
    @param default: default value if variable couldn't be loaded
    @param config_dict: json-like dict
    @return value of env variable or default value
    """

    env_value = os.getenv(key)  # get key from environment

    # try to get key also from config file
    conf_val = None
    if isinstance(config_dict, dict):
        conf_val = config_dict.get(key, None)

    # Decide which value to take
    if env_value and conf_val:
        logger.info(f"Gained '{key}' from environment and config - preferring env-variable")
        value = env_value
    elif env_value:
        logger.debug(f"Gained '{key}' from environment only, using this value")
        value = env_value
    elif conf_val:
        logger.debug(f"Gained '{key}' from config-file only, using this value")
        value = conf_val
    else:
        value = None

    # catch token and prefix value, since it doesn't need the extra replace handling below
    # also PREFIX isn't defined yet...
    if key == "TOKEN":
        return value

    if key == "PREFIX":
        if value:
            return value
        else:
            logger.warning(f"Can't load env-variable for: '{key}' - falling back to DEFAULT {key}='{default}'")
            return default

    if value is not None:
        try:
            return value.replace("{PREFIX}", PREFIX)
        # this happens when a variable is loaded before PREFIX
        except NameError as e:
            logger.error(
                f"Can't replace expressions for: '{key}' {e.__repr__()}.\n"
                f"This happens if a referenced env-variable isn't initiated yet. "
                f"You may wanna change the load order - falling back to DEFAULT {key}='{default}' "
            )
            return default
    logger.warning(f"Can't load env-variable for: '{key}' - falling back to DEFAULT {key}='{default}'")
    return default


def load_conf_file(config_file='./data/config.json') -> Optional[Dict[str, str]]:
    if os.path.isfile(config_file):
        logger.debug(f"Config file '{config_file}' exists, trying to read")
        try:
            with open(config_file, "r") as jsonfile:
                return json.load(jsonfile)

        except OSError:
            logger.warning(f"Can't open or read config file: '{config_file}'")

    else:
        logger.debug(f"No config-file was found under '{config_file}', trying to continue")


cfg_dict = load_conf_file('./data/config.json')

TOKEN = load_env("TOKEN", '', config_dict=cfg_dict)  # reading in the token from environment - there is no default...

# loading optional env variables
PREFIX = load_env("PREFIX", "b!", config_dict=cfg_dict)
OWNER_NAME = load_env("OWNER_NAME", "unknown", config_dict=cfg_dict)  # owner name with tag e.g. pi#3141
OWNER_ID = int(load_env("OWNER_ID", "100000000000000000", config_dict=cfg_dict))  # discord id of the owner
ACTIVITY_NAME = load_env("ACTIVITY_NAME", f"{PREFIX}help", config_dict=cfg_dict)  # activity bot plays

# roles to give on verification
_ROLES = os.getenv('ROLES', "760434164146634752")
GUILD = int(load_env("GUILD", "760421261649248296"))  # guild the bot is configured for
START_CHANNEL = int(load_env("START_CHANNEL", "760429072156459019"))  # channel to point members to after verification
ONBOARDING_CHANNEL = int(load_env("ONBOARDING_CHANNEL", "1015975768045670501"))  # channel for interaction button
ONBOARDING_ROLE = int(load_env("ONBOARDING_ROLE", "1015975563250372698"))  # member has this only during onboarding
# date after which members need to be joined so that the bot will capture their not pending but role-less existence
_NOT_BEFORE = load_env("NOT_BEFORE", "25.08.2021")
NOT_BEFORE = datetime.strptime(_NOT_BEFORE, "%d.%m.%Y")

CHECK_PERIOD = int(load_env("CHECK_PERIOD", "5"))

# rough sanity check if roles were given
if not _ROLES:
    error = "Can't load env-variable ROLES - Bot needs at least one role-id to start!\n"
    logger.error(error)
    raise KeyError(error)

ROLES = [int(role.strip()) for role in _ROLES.split(' ')]
