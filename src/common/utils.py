import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Environment variable {var_name} is missing")
    return value
