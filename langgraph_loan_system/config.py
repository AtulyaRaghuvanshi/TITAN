import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


APP_NAME = os.getenv("APP_NAME", "Multi-Agent Loan Approval System")
MIN_CREDIT_SCORE = env_int("MIN_CREDIT_SCORE", 700)
MAX_FOIR_PERCENT = env_int("MAX_FOIR_PERCENT", 50)
MIN_MONTHLY_INCOME = env_int("MIN_MONTHLY_INCOME", 25000)
REQUIRED_DOCUMENTS = [
    name
    for name, required in {
        "pan": env_bool("REQUIRE_PAN", True),
        "aadhaar": env_bool("REQUIRE_AADHAAR", True),
        "bank_statement": env_bool("REQUIRE_BANK_STATEMENT", True),
    }.items()
    if required
]
SANCTION_OUTPUT_DIR = Path(os.getenv("SANCTION_OUTPUT_DIR", BASE_DIR / "generated_sanctions"))

