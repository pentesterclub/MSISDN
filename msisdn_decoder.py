#!/usr/bin/env python3
"""
msisdn_decoder.py
=================

Decode an MSISDN into CC / NDC / SN and produce a best-effort guess at
the operator's MCC / MNC.

INSTALL:
    pip install phonenumbers

USAGE:
    python msisdn_decoder.py "+14155552671"
    python msisdn_decoder.py "+447911123456"
    python msisdn_decoder.py "+919876543210"

IMPORTANT:
    The MSIN portion of an IMSI is operator-internal. You CANNOT recover
    the full IMSI from an MSISDN alone — the mapping lives in the
    operator's HLR/HSS. This tool gives you a *plausible* MCC + carrier
    hint, nothing more.
"""

import sys
import json
import phonenumbers
from phonenumbers import geocoder, carrier, NumberParseException


# ---------------------------------------------------------------------------
# CC -> list of plausible MCCs in that country.
#
# Real-world: a country can have many MCCs (test ranges, MVNOs, old
# allocations, etc.). We list the primary ones only. For a full list, see
# the ITU-T E.212 MCC assignment table.
# ---------------------------------------------------------------------------
CC_TO_MCC = {
    1:   ["310", "311", "312", "313", "314", "315", "316"],   # US/CA/Caribbean
    7:   ["250", "251", "252", "255"],                         # RU / KZ
    20:  ["602", "603"],                                       # EG
    27:  ["655"],                                              # ZA
    30:  ["202"],                                              # GR
    31:  ["204"],                                              # NL
    32:  ["206"],                                              # BE
    33:  ["208"],                                              # FR
    34:  ["214", "216"],                                       # ES
    36:  ["216"],                                              # HU
    39:  ["222", "22210"],                                     # IT
    40:  ["226"],                                              # RO
    41:  ["228"],                                              # CH
    43:  ["232"],                                              # AT
    44:  ["234", "235"],                                       # GB
    45:  ["238"],                                              # DK
    46:  ["240", "241", "244"],                                # SE
    47:  ["242"],                                              # NO
    48:  ["260"],                                              # PL
    49:  ["262"],                                              # DE
    51:  ["716"],                                              # PE
    52:  ["334", "335"],                                       # MX
    54:  ["722", "724"],                                       # AR
    55:  ["724", "726"],                                       # BR
    56:  ["730", "732"],                                       # CL
    57:  ["732", "734"],                                       # CO
    60:  ["502", "510", "511", "515"],                         # MY
    61:  ["502", "505", "510", "530"],                         # AU
    62:  ["510", "511", "514"],                                # ID
    63:  ["515", "520", "525"],                                # PH
    64:  ["530", "539"],                                       # NZ
    65:  ["525", "528", "529"],                                # SG
    66:  ["520", "521", "522", "523", "524", "525"],           # TH
    81:  ["440", "441", "450"],                                # JP
    82:  ["450", "451", "452"],                                # KR
    84:  ["452", "454", "455"],                                # VN
    86:  ["460", "461"],                                       # CN
    90:  ["286"],                                              # TR
    91:  ["404", "405", "406", "410"],                         # IN
    92:  ["410", "412", "413", "414", "415"],                  # PK
    93:  ["412", "413", "414", "415", "416", "417"],           # AF
    94:  ["413"],                                              # LK
    95:  ["414", "415", "416"],                                # MM
    98:  ["432", "434", "435", "436", "437"],                  # IR
    211: ["650"],                                              # SS
    212: ["604"],                                              # MA
    213: ["603"],                                              # DZ
    216: ["605"],                                              # TN
    218: ["609"],                                              # LY
    234: ["621"],                                              # NG
    249: ["620"],                                              # SD
    250: ["635"],                                              # RW
    251: ["636"],                                              # ET
    252: ["637"],                                              # SO
    253: ["638"],                                              # DJ
    254: ["639"],                                              # KE
    255: ["640"],                                              # TZ
    256: ["641"],                                              # UG
    257: ["642"],                                              # BI
    258: ["643"],                                              # MZ
    260: ["645"],                                              # ZM
    261: ["646"],                                              # MG
    263: ["648"],                                              # ZW
    880: ["470", "471", "472", "473", "474", "475"],           # BD
    886: ["466", "467"],                                       # TW
    960: ["472"],                                              # MV
    965: ["419"],                                              # KW
    966: ["420", "421"],                                       # SA
    968: ["422"],                                              # OM
    971: ["424", "425", "426", "427"],                         # AE
    972: ["425", "426", "427", "428"],                         # IL
    973: ["426"],                                              # BH
    974: ["427"],                                              # QA
    977: ["429"],                                              # NP
}


# ---------------------------------------------------------------------------
# Country-specific NDC length (digits after CC).
# Used to split the national number into NDC + SN.
# Not exhaustive — defaults to 3 if the country is unknown.
# ---------------------------------------------------------------------------
NDC_LEN_BY_CC = {
    1:   3,   # US/CA: area code = NDC
    7:   3,   # RU
    20:  2,   # EG
    27:  2,   # ZA
    30:  4,   # GR
    31:  2,   # NL
    32:  3,   # BE
    33:  1,   # FR (often 1-digit NDC, e.g. 6, 7 for mobile)
    34:  3,   # ES
    39:  3,   # IT
    44:  4,   # UK (e.g. 7911 for O2)
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
    234: 3,   # NG
    254: 3,   # KE
    255: 3,   # TZ
    880: 3,   # BD
    886: 3,   # TW
    966: 3,   # SA
    971: 2,   # AE
    972: 2,   # IL
    973: 2,   # BH
    974: 2,   # QA
    965: 2,   # KW
    968: 2,   # OM
}


def split_national(national_str: str, cc: int) -> tuple[str, str]:
    """Split a national number string into (NDC, SN)."""
    ndc_len = NDC_LEN_BY_CC.get(cc, 3)
    if ndc_len >= len(national_str):
        ndc_len = max(1, len(national_str) // 2)
    return national_str[:ndc_len], national_str[ndc_len:]


def decode(msisdn: str) -> dict:
    """Decode an MSISDN string. Returns a dict with all parsed fields."""
    out = {
        "input": msisdn,
        "valid_e164": False,
        "cc": None,
        "country_name": None,
        "ndc": None,
        "sn": None,
        "carrier_hint": None,
        "mcc_candidates": [],
        "mnc_guess": "UNKNOWN — requires operator/MCC-MNC database",
        "msin_guess": "IMPOSSIBLE — MSIN is operator-internal",
        "imsi_full_guess": "IMPOSSIBLE without HLR/HSS lookup",
        "warning": (
            "MSISDN does NOT uniquely determine IMSI. The MSIN portion "
            "is operator-assigned and not derivable from the phone number. "
            "Use this tool for educational / format-checking only."
        ),
    }

    try:
        parsed = phonenumbers.parse(msisdn, None)
    except NumberParseException as e:
        out["error"] = str(e)
        return out

    cc = parsed.country_code
    national = str(parsed.national_number)
    ndc, sn = split_national(national, cc)

    out["cc"] = cc
    out["country_name"] = geocoder.description_for_number(parsed, "en") or "Unknown"
    out["ndc"] = ndc
    out["sn"] = sn
    out["carrier_hint"] = carrier.name_for_number(parsed, "en") or "Unknown"
    out["mcc_candidates"] = CC_TO_MCC.get(cc, [])
    out["valid_e164"] = phonenumbers.is_valid_number(parsed)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    result = decode(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
