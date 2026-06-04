"""
data/mcc_mnc.py
===============

Loads the bundled comprehensive MCC-MNC-operator dataset from
``mcc_mnc_full.json`` and exposes the same API used by the decoder.

The bundled JSON contains 2716+ records across 231 countries, sourced
from the public mcc-mnc-list repository (which mirrors the live ITU-T
E.212 assignments).  The dataset uses ISO 3166-1 alpha-2 country codes;
we bridge to ITU-T E.164 country calling codes via ``data/iso_to_cc.py``.

Schema of one record (from mcc_mnc_full.json):

    {
      "type":        "National",
      "countryName": "India",
      "countryCode": "IN",
      "mcc":         "404",
      "mnc":         "10",
      "brand":       "Airtel",
      "operator":    "Bharti Airtel Limited",
      "status":      "Operational",
      "bands":       "GSM 900 / LTE 1800 / LTE 2100 / 5G NR",
      "notes":       null
    }

Developer: pentesterclub
"""

from __future__ import annotations
import json
import os
from typing import Optional

import iso_to_cc


# ---------------------------------------------------------------------------
# Load the bundled JSON at import time.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH = os.path.join(_HERE, "mcc_mnc_full.json")

with open(_JSON_PATH, "r", encoding="utf-8") as _f:
    _RAW_DATA: list[dict] = json.load(_f)


# Normalize into a consistent internal shape and build indexes.
# Each record becomes:
#   {
#     "mcc": "404", "mnc": "10",
#     "operator": "Airtel", "brand": "Airtel",
#     "country": "India", "iso": "IN", "cc": 91,
#     "status": "Operational", "bands": "..."
#   }
def _normalize(rec: dict) -> Optional[dict]:
    mcc = (rec.get("mcc") or "").strip()
    mnc = (rec.get("mnc") or "").strip().zfill(2)  # zero-pad to 2 digits for matching
    if not mcc or not mnc:
        return None
    iso = (rec.get("countryCode") or "").strip()
    cc = iso_to_cc.get(iso) if iso else None
    return {
        "mcc": mcc,
        "mnc": mnc,
        "operator": (rec.get("operator") or rec.get("brand") or "Unknown").strip(),
        "brand":    (rec.get("brand") or rec.get("operator") or "Unknown").strip(),
        "country":  (rec.get("countryName") or "").strip(),
        "iso":      iso,
        "cc":       cc,
        "status":   (rec.get("status") or "").strip(),
        "bands":    (rec.get("bands") or "").strip(),
        "notes":    (rec.get("notes") or "").strip(),
    }


MCC_MNC_TABLE: list[dict] = [r for r in (_normalize(x) for x in _RAW_DATA) if r]

# Indexes for fast lookup
_BY_MCC_MNC: dict[tuple[str, str], dict] = {
    (row["mcc"], row["mnc"]): row for row in MCC_MNC_TABLE
}

# CC (E.164) -> list of MCCs used in that country.
CC_TO_MCCS: dict[int, list[str]] = {}
for row in MCC_MNC_TABLE:
    cc = row.get("cc")
    if cc is None:
        continue
    CC_TO_MCCS.setdefault(cc, [])
    if row["mcc"] not in CC_TO_MCCS[cc]:
        CC_TO_MCCS[cc].append(row["mcc"])


# ---------------------------------------------------------------------------
# Region disambiguation table (ISO region -> MCC) for shared +1 country code.
# Used by the decoder to pick US vs Canada vs Caribbean.
# ---------------------------------------------------------------------------
REGION_TO_MCC: dict[str, tuple[str, str]] = {
    "US": ("310", "United States of America"),
    "CA": ("302", "Canada"),
    "PR": ("330", "Puerto Rico"),
    "VI": ("332", "United States Virgin Islands"),
    "JM": ("338", "Jamaica"),
    "GU": ("310", "Guam"),
    "AS": ("311", "American Samoa"),
    "MP": ("310", "Northern Mariana Islands"),
    "DO": ("370", "Dominican Republic"),
    "TT": ("374", "Trinidad and Tobago"),
    "BS": ("364", "Bahamas"),
    "BB": ("342", "Barbados"),
    "HT": ("372", "Haiti"),
    "GD": ("352", "Grenada"),
    "LC": ("358", "Saint Lucia"),
    "DM": ("366", "Dominica"),
    "VC": ("360", "Saint Vincent and the Grenadines"),
    "AG": ("344", "Antigua and Barbuda"),
    "KN": ("356", "Saint Kitts and Nevis"),
    "TC": ("376", "Turks and Caicos Islands"),
    "AI": ("365", "Anguilla"),
    "MS": ("354", "Montserrat"),
    "VG": ("348", "British Virgin Islands"),
    "KY": ("346", "Cayman Islands"),
    "BM": ("350", "Bermuda"),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def mccs_for_cc(cc: int) -> list[str]:
    """Return plausible MCCs for an E.164 country code."""
    return CC_TO_MCCS.get(cc, [])


def lookup(mcc: str, mnc: str) -> Optional[dict]:
    """Look up a (MCC, MNC) -> operator record, or None."""
    mnc_padded = (mnc or "").strip().zfill(2)
    return _BY_MCC_MNC.get((mcc, mnc_padded)) or _BY_MCC_MNC.get((mcc, mnc))


def lookup_by_carrier(cc: int, carrier_name: str) -> list[dict]:
    """
    Given a country code and a carrier name, return all (MCC, MNC,
    operator) rows in that country whose brand/operator matches.
    """
    if not carrier_name:
        return []
    carrier_lc = carrier_name.lower().strip()
    out: list[dict] = []
    for row in MCC_MNC_TABLE:
        if row.get("cc") != cc:
            continue
        op = (row.get("operator") or "").lower()
        br = (row.get("brand") or "").lower()
        if (carrier_lc in op or op in carrier_lc
                or carrier_lc in br or br in carrier_lc):
            out.append(row)
    return out


def lookup_by_region(region_code: str) -> Optional[dict]:
    """
    Look up an MCC entry by ISO 2-letter region code (e.g. 'US', 'CA').
    Used to disambiguate within shared country codes like +1.
    """
    if not region_code:
        return None
    region_code = region_code.upper()
    if region_code in REGION_TO_MCC:
        mcc, country = REGION_TO_MCC[region_code]
        return {"mcc": mcc, "mnc": None, "operator": None,
                "country": country, "cc": 1}
    return None


def all_records() -> list[dict]:
    """Return the full normalized table (for inspection / tests)."""
    return MCC_MNC_TABLE
