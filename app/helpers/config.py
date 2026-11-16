"""Server settings; every knob lives here and can be overridden by environment variable."""
import os

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/tmp/server.sqlite3")
SCHEMA_STATEMENTS = [
    """
    CREATE TABLE members (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE plans (
        id TEXT PRIMARY KEY,
        country TEXT NOT NULL,
        currency TEXT NOT NULL,
        monthly INTEGER NOT NULL,
        joining_fee INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE agreements (
        id TEXT PRIMARY KEY,
        member_id TEXT NOT NULL REFERENCES members (id),
        plan_id TEXT NOT NULL REFERENCES plans (id),
        start_date TEXT NOT NULL,
        due_day INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE reconciliation_runs (
        id TEXT PRIMARY KEY,
        body TEXT NOT NULL
    )
    """,
]

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

PHONE_CHARACTERS_TO_REMOVE = " -()"  # space, hyphen, round brackets

MEMBER_NAME_MIN_LENGTH = 1
MEMBER_NAME_MAX_LENGTH = 120

# The countries table; in the mobile masks X is any digit and spaces are only for reading.
COUNTRY_TABLE = [
    {
        "name": "United Arab Emirates",
        "code": "AE",
        "dial_code": "971",
        "currency": "AED",
        "minor_unit": "fils",
        "minor_units_per_unit": 100,
        "vat_percent": 5,
        "national_mobile": "05X XXX XXXX",
        "e164_mobile": "+9715XXXXXXXX",
    },
    {
        "name": "Saudi Arabia",
        "code": "SA",
        "dial_code": "966",
        "currency": "SAR",
        "minor_unit": "halalas",
        "minor_units_per_unit": 100,
        "vat_percent": 15,
        "national_mobile": "05X XXX XXXX",
        "e164_mobile": "+9665XXXXXXXX",
    },
    {
        "name": "Bahrain",
        "code": "BH",
        "dial_code": "973",
        "currency": "BHD",
        "minor_unit": "fils",
        "minor_units_per_unit": 1000,
        "vat_percent": 10,
        "national_mobile": "3XXX XXXX",
        "e164_mobile": "+9733XXXXXXX",
    },
]

DUE_DAY_MIN = 1
DUE_DAY_MAX = 31
MAX_INVOICE_RANGE_DAYS = 366  # to may be at most this many days after from

AMOUNT_TOLERANCE_MINOR_UNITS = 1  # a settled amount matches an invoice total this close to it
