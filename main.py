import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_yaml():
    path = Path("config.development.yaml")
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # Layer 2 - YAML
    config.update(load_yaml())

    # Layer 3 - .env ONLY
    env_file = dotenv_values(".env")

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_name, key in mapping.items():
        if env_name in env_file:
            config[key] = coerce(key, env_file[env_name])

    # Layer 4 - OS Environment
    for env_name, key in mapping.items():
        if env_name in os.environ:
            config[key] = coerce(key, os.environ[env_name])

    # Layer 5 - CLI overrides
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        config[key] = coerce(key, value)

    config["api_key"] = "****"

    return config