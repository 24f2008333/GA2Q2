import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Load .env
load_dotenv()

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default configuration
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_yaml():
    filename = "config.development.yaml"

    if not Path(filename).exists():
        return {}

    with open(filename, "r") as f:
        data = yaml.safe_load(f) or {}

    return data


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # YAML layer
    config.update(load_yaml())

    # .env / OS environment
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_name, key in mapping.items():
        value = os.getenv(env_name)
        if value is not None:
            config[key] = coerce(key, value)

    # CLI overrides (?set=key=value)
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        config[key] = coerce(key, value)

    # Mask secret
    config["api_key"] = "****"

    return config