"""
decoder.py
==========

Core MSISDN -> (CC, NDC, SN) + best-effort (MCC, MNC, MSIN) decoder.

Public API:
    decode(msisdn: str) -> dict

Author: pentesterclub
Version: 1.1.0
"""

from __future__ import annotations
from typing import Optional
import phonenumbers
from phonenumbers import geocoder, carrier, NumberParseException

import mcc_mnc
import carriers


__author__    = "pentesterclub"
__version__   = "1.1.0"
__tool_name__ = "MSISDN Decoder"


# ---------------------------------------------------------------------------
# Country-specific NDC length (digits after the country code).
# Used to split the national number into NDC + SN.
# Defaults to 3 if the country is unknown.
# ---------------------------------------------------------------------------
NDC_LEN_BY_CC: dict[int, int] = {
    1:   3,   # NANP (US/CA/Caribbean)
    7:   3,   # RU / KZ
    20:  2,   # EG
    27:  2,   # ZA
    30:  4,   # GR
    31:  2,   # NL
    32:  3,   # BE
    33:  1,   # FR (often 1-digit NDC for mobile)
    34:  3,   # ES
    39:  3,   # IT
    44:  4,   # UK
    46:  3,   # SE
    47:  3,   # NO
    48:  2,   # PL
    49:  3,   # DE
    51:  2,   # PE
    52:  2,   # MX
    54:  4,   # AR
    55:  2,   # BR
    56:  2,   # CL
    57:  3,   # CO
    60:  2,   # MY
    61:  2,   # AU
    62:  3,   # ID
    63:  3,   # PH
    64:  2,   # NZ
    65:  2,   # SG
    66:  2,   # TH
    81:  3,   # JP
    82:  3,   # KR
    84:  3,   # VN
    86:  3,   # CN
    90:  3,   # TR
    91:  4,   # IN
    92:  3,   # PK
    93:  3,   # AF
    94:  3,   # LK
    95:  3,   # MM
    98:  3,   # IR
    211: 3,   # SS
    212: 3,   # MA
    213: 3,   # DZ
    216: 2,   # TN
    218: 3,   # LY
    220: 2,   # GM
    221: 2,   # SN
    234: 3,   # NG
    249: 2,   # SD
    250: 3,   # RW
    251: 2,   # ET
    252: 2,   # SO
    253: 2,   # DJ
    254: 3,   # KE
    255: 3,   # TZ
    256: 3,   # UG
    257: 2,   # BI
    258: 2,   # MZ
    260: 2,   # ZM
    261: 2,   # MG
    263: 3,   # ZW
    264: 2,   # NA
    265: 2,   # MW
    266: 2,   # LS
    267: 2,   # BW
    268: 2,   # SZ
    880: 3,   # BD
    886: 3,   # TW
    960: 3,   # MV
    961: 2,   # LB
    962: 2,   # JO
    963: 2,   # SY
    964: 2,   # IQ
    965: 2,   # KW
    966: 3,   # SA
    967: 2,   # YE
    968: 2,   # OM
    970: 3,   # PS
    971: 2,   # AE
    972: 2,   # IL
    973: 2,   # BH
    974: 2,   # QA
    975: 2,   # BT
    976: 2,   # MN
    977: 3,   # NP
    992: 2,   # TJ
    993: 2,   # TM
    994: 2,   # AZ
    995: 3,   # GE
    996: 2,   # KG
    998: 2,   # UZ
}


def split_national(national_str: str, cc: int) -> tuple[str, str]:
    """Split a national number string into (NDC, SN)."""
    ndc_len = NDC_LEN_BY_CC.get(cc, 3)
    if ndc_len >= len(national_str):
        ndc_len = max(1, len(national_str) // 2)
    return national_str[:ndc_len], national_str[ndc_len:]


def _choose_mcc_mnc(
    cc: int,
    mcc_candidates: list[str],
    carrier_canon: Optional[str],
    region: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Pick the best (MCC, MNC, operator) given a country code, list of
    candidate MCCs, a normalized carrier name, and an optional ISO
    region code.
    """
    if not mcc_candidates:
        return None, None, None

    # 1. Region hint wins for shared country codes (+1 NANP, etc.)
    if region and cc == 1:
        region_entry = mcc_mnc.lookup_by_region(region)
        if region_entry and region_entry["mcc"] in mcc_candidates:
            preferred_mcc = region_entry["mcc"]
            if carrier_canon:
                for row in mcc_mnc.MCC_MNC_TABLE:
                    if row["mcc"] == preferred_mcc and row["cc"] == cc:
                        if (carrier_canon.lower() in row["operator"].lower()
                                or row["operator"].lower() in carrier_canon.lower()):
                            return row["mcc"], row["mnc"], row["operator"]
            for row in mcc_mnc.MCC_MNC_TABLE:
                if row["mcc"] == preferred_mcc and row["cc"] == cc:
                    return row["mcc"], row["mnc"], row["operator"]
            return preferred_mcc, None, None

    # 2. Carrier hint
    if carrier_canon:
        matches = mcc_mnc.lookup_by_carrier(cc, carrier_canon)
        if matches:
            for row in matches:
                if row["mcc"] in mcc_candidates:
                    return row["mcc"], row["mnc"], row["operator"]
            row = matches[0]
            return row["mcc"], row["mnc"], row["operator"]

    # 3. Fallback: first candidate MCC, first row for that MCC
    for mcc in mcc_candidates:
        for row in mcc_mnc.MCC_MNC_TABLE:
            if row["mcc"] == mcc and row["cc"] == cc:
                return row["mcc"], row["mnc"], row["operator"]

    return mcc_candidates[0], None, None


def decode(msisdn: str) -> dict:
    """
    Decode an MSISDN into its parts and attempt a best-effort
    (MCC, MNC, operator) lookup against the bundled global dataset.

    Returns a dict with keys:
        input, valid, error,
        cc, country, region, ndc, sn, national_number, e164_format,
        mcc, mnc, operator, msin_guess, imsi_partial,
        mcc_candidates, carrier_raw, carrier_canonical,
        mnc_options (list of {mcc, mnc, operator, brand, status, bands}),
        msn_status, warning
    """
    result: dict = {
        "input": msisdn,
        "valid": False,
        "error": None,

        # --- MSISDN components ---
        "cc": None,
        "country": None,
        "region": None,
        "ndc": None,
        "sn": None,
        "national_number": None,
        "e164_format": None,

        # --- IMSI components (best-effort) ---
        "mcc": None,
        "mnc": None,
        "operator": None,
        "operator_full": None,
        "msin_guess": None,
        "imsi_partial": None,
        "imsi_status": "NOT_DERIVABLE",
        "msn_status": "NOT_DERIVABLE",
        "msn_explanation": (
            "MSIN is assigned by the operator internally. The mapping "
            "lives in the HLR/HSS subscriber database and cannot be "
            "recovered from an MSISDN."
        ),

        # --- Metadata ---
        "mcc_candidates": [],
        "carrier_raw": None,
        "carrier_canonical": None,
        "region_code": None,
        "mnc_options": [],

        "warning": (
            "MSISDN does NOT uniquely determine IMSI. The MSIN portion is "
            "operator-internal. MCC and MNC here are best-effort guesses "
            "based on country code + carrier name and the bundled global "
            "MCC-MNC dataset."
        ),
        "_meta": {
            "tool": __tool_name__,
            "author": __author__,
            "version": __version__,
        },
    }

    # ---------- 1. Parse with libphonenumber ----------
    try:
        parsed = phonenumbers.parse(msisdn, None)
    except NumberParseException as e:
        result["error"] = str(e)
        return result

    cc = parsed.country_code
    national = str(parsed.national_number)
    ndc, sn = split_national(national, cc)

    raw_carrier = carrier.name_for_number(parsed, "en") or ""
    region_text = geocoder.description_for_number(parsed, "en") or ""

    try:
        from phonenumbers import region_code_for_number
        region_code = region_code_for_number(parsed)
    except Exception:
        region_code = None

    country_name = ""
    if region_code:
        # Try to map region code to a human-friendly name via our dataset
        for row in mcc_mnc.MCC_MNC_TABLE:
            if row.get("iso") == region_code and row.get("country"):
                country_name = row["country"]
                break
        if not country_name:
            country_name = region_code

    result["cc"] = cc
    result["country"] = country_name or region_code or "Unknown"
    result["region"] = region_text
    result["ndc"] = ndc
    result["sn"] = sn
    result["national_number"] = national
    result["e164_format"] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    result["valid"] = phonenumbers.is_valid_number(parsed)
    result["carrier_raw"] = raw_carrier
    result["carrier_canonical"] = carriers.normalize(raw_carrier) if raw_carrier else None
    result["mcc_candidates"] = mcc_mnc.mccs_for_cc(cc)
    result["region_code"] = region_code

    # ---------- 2. Best-effort (MCC, MNC, operator) ----------
    mcc, mnc, op = _choose_mcc_mnc(
        cc, result["mcc_candidates"], result["carrier_canonical"], region_code
    )
    result["mcc"] = mcc
    result["mnc"] = mnc
    if op:
        # Look up the full row to get brand / status / bands
        full = mcc_mnc.lookup(mcc, mnc)
        if full:
            raw_brand = full.get("brand") or op
            result["operator"] = carriers.clean_dataset_brand(raw_brand) or raw_brand
            result["operator_full"] = full.get("operator")
        else:
            result["operator"] = op

    # Build a list of plausible (MCC, MNC, operator) options for the user.
    if result["carrier_canonical"]:
        all_matches = mcc_mnc.lookup_by_carrier(cc, result["carrier_canonical"])
        seen = set()
        result["mnc_options"] = []
        for r in all_matches:
            key = (r["mcc"], r["mnc"])
            if key in seen:
                continue
            seen.add(key)
            raw_brand = r.get("brand") or r.get("operator")
            result["mnc_options"].append({
                "mcc": r["mcc"], "mnc": r["mnc"],
                "operator": carriers.clean_dataset_brand(raw_brand) or raw_brand,
                "operator_full": r.get("operator"),
                "status": r.get("status"),
                "bands": r.get("bands"),
            })

    # ---------- 3. Build the partial IMSI template ----------
    if mcc and mnc:
        msin_len = 15 - len(mcc) - len(mnc)
        msin_len = max(1, msin_len)
        result["msin_guess"] = "?" * msin_len + "  (NOT derivable from MSISDN)"
        result["imsi_partial"] = f"{mcc}-{mnc}-{'X' * msin_len}"
        result["imsi_status"] = "PARTIAL"
        result["msn_status"] = "NOT_DERIVABLE"

    return result
