"""User configuration: a one-time interactive setup per backend, stored
under the platform's standard config directory, with env-var overrides
for power users."""

import os
import tomllib
from pathlib import Path

from .backends import get_backend

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "scribe"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"


def _read_raw_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def _write_raw_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        for key, value in config.items():
            f.write(f'{key} = "{value}"\n')
    print(f"Saved config to {CONFIG_FILE}")


def run_first_time_setup(backend_name: str, existing: dict) -> dict:
    backend = get_backend(backend_name)
    print(f"First-time setup for the '{backend_name}' backend.\n")

    config = dict(existing)  # keep any other backends' settings already saved
    config["openrouter_api_key"] = input("Enter your OpenRouter API key: ").strip() or existing.get(
        "openrouter_api_key", ""
    )
    config["model"] = input(f"Model to use [{DEFAULT_MODEL}]: ").strip() or existing.get(
        "model", DEFAULT_MODEL
    )

    for key in backend.required_config_keys:
        prompt = backend.setup_prompts.get(key, f"Enter {key}: ")
        config[key] = input(prompt).strip()

    _write_raw_config(config)
    return config


def load_config(backend_name: str, force_setup: bool = False) -> dict:
    backend = get_backend(backend_name)
    existing = _read_raw_config()

    missing_keys = [k for k in backend.required_config_keys if not existing.get(k)]
    if force_setup or not existing or missing_keys:
        config = run_first_time_setup(backend_name, existing)
    else:
        config = existing

    # Env vars always win, for power users / CI / testing.
    config["openrouter_api_key"] = os.environ.get(
        "OPENROUTER_API_KEY", config.get("openrouter_api_key")
    )
    config["model"] = os.environ.get("AGENT_MODEL", config.get("model", DEFAULT_MODEL))
    for key in backend.required_config_keys:
        env_var = key.upper()
        config[key] = os.environ.get(env_var, config.get(key))

    missing = ["openrouter_api_key"] + backend.required_config_keys
    missing = [k for k in missing if not config.get(k)]
    if missing:
        raise ValueError(
            f"Missing required config: {', '.join(missing)}. "
            f"Run 'scribe {backend_name} config --reset' to set up again."
        )
    return config