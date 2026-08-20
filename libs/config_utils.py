import os
import importlib.util
from addict import Dict
from .log_utils import get_logger

DEFAULT_ENV = 'stage'  # stage, demo
DEFAULT_TERRITORY = 'tw'
DEFAULT_DEVICE_PLATFORM = 'android'  # android, ios
DEFAULT_DEVICE_TARGET = 'device'  # emulator, device
_logger = get_logger(__name__)


def _get_config_module(file_path):
    spec = importlib.util.spec_from_file_location("config_variables", file_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    return config_module


def _get_env(site_env):
    if site_env:
        return site_env

    return os.environ.get("SITE_ENV") or DEFAULT_ENV


def _get_territory(site_territory):
    if site_territory:
        return site_territory

    return os.environ.get("SITE_TERRITORY") or DEFAULT_TERRITORY


def _get_language(default_language):
    return os.environ.get("SITE_LANG") or default_language


def _get_device_platform(device_platform):
    if device_platform:
        return device_platform

    return os.environ.get("DEVICE_PLATFORM") or DEFAULT_DEVICE_PLATFORM


def _get_device_target(device_target):
    if device_target:
        return device_target

    return os.environ.get("DEVICE_TARGET") or DEFAULT_DEVICE_TARGET


def _module_to_dict(module):
    return {
        variable_name: getattr(module, variable_name)
        for variable_name in dir(module)
        if not variable_name.startswith("__")
    }


def get_config(territory=None, env=None):
    env = _get_env(env)
    territory = _get_territory(territory)
    _logger.info(f'territory - {territory}')
    working_dir = os.getcwd()
    api_variables_file_path = f"{working_dir}/variables/api.py"
    _logger.debug(f"load api variables file from {api_variables_file_path}")
    
    api_variables_module = _get_config_module(api_variables_file_path)
    variable_dict = _module_to_dict(api_variables_module)

    env_config_file_path = f"{working_dir}/variables/site_{env}_{territory}.py"
    _logger.debug(f"load env variables file from {env_config_file_path}")

    env_config_module = _get_config_module(env_config_file_path)
    variable_dict.update(_module_to_dict(env_config_module))

    py_language = variable_dict['services']['accept_language']
    variable_dict['services']['accept_language'] = _get_language(py_language)
    return Dict(variable_dict)

def get_capabilities(platform=None, target=None):
    """讀取 `variables/capabilities/{platform}_{target}.py` 的 Appium desired capabilities。

    以 DEVICE_PLATFORM（android/ios）與 DEVICE_TARGET（emulator/device）兩個環境變數切換，
    預設走 android_emulator，方便本機開發；跑實體機時另外指定環境變數即可。
    """
    platform = _get_device_platform(platform)
    target = _get_device_target(target)
    _logger.info(f'device capabilities - {platform}_{target}')
    working_dir = os.getcwd()
    capabilities_file_path = f"{working_dir}/variables/capabilities/{platform}_{target}.py"
    _logger.debug(f"load capabilities file from {capabilities_file_path}")

    capabilities_module = _get_config_module(capabilities_file_path)
    return Dict(capabilities_module.capabilities)


config = get_config()
