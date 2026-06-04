"""
data/carriers.py
================

Normalize carrier names returned by `phonenumbers.carrier.name_for_number()`
to the operator names used in our MCC-MNC database.

libphonenumber returns strings like:
    "Airtel", "Reliance Jio", "Vodafone", "T-Mobile", "O2", "EE", "JT",
    "China Mobile", "Verizon", "AT&T", "Movistar", etc.

We map them to a canonical operator name so we can find matching rows
in mcc_mnc.MCC_MNC_TABLE.
"""

from __future__ import annotations
import re


# Carrier name returned by libphonenumber -> canonical operator name
# (used to look up matching rows in mcc_mnc.MCC_MNC_TABLE).
CARRIER_ALIASES: dict[str, str] = {
    # India
    "airtel":               "Airtel",
    "bharti airtel":        "Airtel",
    "reliance jio":         "Jio",
    "jio":                  "Jio",
    "vodafone":             "Vodafone",
    "vi":                   "Vodafone",
    "idea":                 "Vodafone",
    "bsnl":                 "BSNL",
    "bsnl mobile":          "BSNL",
    "mtnl":                 "MTNL",
    "tata docomo":          "Tata Docomo",
    "tata teleservices":    "Tata Docomo",
    "docomo":               "Tata Docomo",

    # UK
    "o2":                   "O2",
    "ee":                   "EE",
    "everything everywhere": "EE",
    "vodafone uk":          "Vodafone",
    "three":                "Three",
    "hutchison":            "Three",
    "h3g":                  "Three",
    "jt":                   "JT",

    # USA
    "verizon":              "Verizon",
    "at&t":                 "AT&T",
    "t-mobile":             "T-Mobile",
    "tmobile":              "T-Mobile",
    "sprint":               "Sprint",
    "us cellular":          "US Cellular",
    "metro pcs":            "T-Mobile",
    "cricket":              "AT&T",
    "boost mobile":         "Dish",
    "tracfone":             "TracFone",
    "straight talk":        "TracFone",

    # Germany
    "telefonica":           "Telefonica",
    "telefonica (o2)":      "Telefonica",
    "o2 (deu)":             "O2",
    "congstar":             "T-Mobile",
    "1&1":                  "Telefonica",
    "drillisch":            "Telefonica",

    # France
    "orange":               "Orange",
    "sfr":                  "SFR",
    "bouygues telecom":     "Bouygues Telecom",
    "bouygues":             "Bouygues Telecom",
    "free mobile":          "Free Mobile",
    "free":                 "Free Mobile",

    # China
    "china mobile":         "China Mobile",
    "china unicom":         "China Unicom",
    "china telecom":        "China Telecom",

    # Japan
    "ntt docomo":           "NTT Docomo",
    "docomo":               "NTT Docomo",
    "softbank":             "SoftBank",
    "kddi":                 "KDDI",
    "au":                   "KDDI",
    "au by kddi":           "KDDI",

    # Korea
    "sk telecom":           "SK Telecom",
    "kt":                   "KT",
    "olleh":                "KT",
    "lg u+":                "LG U+",
    "lg uplus":             "LG U+",
    "lg telecom":           "LG U+",

    # Australia / NZ
    "telstra":              "Telstra",
    "optus":                "Optus",
    "vodafone au":          "Vodafone",
    "2degrees":             "2degrees",
    "spark":                "Spark",
    "one nz":               "Spark",

    # Canada
    "bell":                 "Bell Mobility",
    "bell mobility":        "Bell Mobility",
    "rogers":               "Rogers Wireless",
    "rogers wireless":      "Rogers Wireless",
    "telus":                "Telus Mobility",
    "telus mobility":       "Telus Mobility",
    "sasktel":              "SaskTel",

    # Singapore
    "singtel":              "SingTel",
    "starhub":              "StarHub",
    "m1":                   "M1",
    "circles.life":         "M1",
    "grid communications":  "Grid",

    # Brazil
    "vivo":                 "Vivo",
    "claro":                "Claro",
    "tim":                  "TIM",
    "tim brasil":           "TIM",
    "oi":                   "Oi",
    "nextel":               "Nextel",

    # Mexico
    "telcel":               "Telcel",
    "america movil":        "Telcel",
    "movistar":             "Movistar",
    "telefonica movistar":  "Movistar",
    "unefon":               "AT&T",

    # South Africa
    "vodacom":              "Vodacom",
    "mtn":                  "MTN",
    "cell c":               "Cell C",
    "telkom mobile":        "Telkom Mobile",

    # UAE
    "etisalat":             "Etisalat",
    "du":                   "du",

    # Saudi Arabia
    "al jawal":             "Al Jawal (STC)",
    "al jawal (stc)":       "Al Jawal (STC)",
    "stc":                  "Al Jawal (STC)",
    "mobily":               "Mobily",
    "zain sa":              "Zain",
    "zain":                 "Zain",
}


def normalize(carrier_name: str) -> str | None:
    """
    Return the canonical operator name for a raw carrier string, or
    None if we don't recognize it.
    """
    if not carrier_name:
        return None
    key = carrier_name.lower().strip()
    # Direct alias
    if key in CARRIER_ALIASES:
        return CARRIER_ALIASES[key]
    # Substring fallback — e.g. "Bharti Airtel (Rajasthan)" -> "Airtel"
    for alias, canonical in CARRIER_ALIASES.items():
        if alias in key or key in alias:
            return canonical
    # Punctuation cleanup fallback
    cleaned = re.sub(r"[^a-z0-9 ]", " ", key)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned in CARRIER_ALIASES:
        return CARRIER_ALIASES[cleaned]
    return None


# Reverse map: dataset-style brand names that are aliases for our canonical names.
# Used to clean up operator names coming from the bundled dataset.
DATASET_BRAND_ALIASES: dict[str, str] = {
    "telekom":                "T-Mobile",
    "telekom deutschland":    "T-Mobile",
    "airtel":                 "Airtel",
    "airtelpunjab":           "Airtel",
    "airtel (mumbai)":        "Airtel",
    "t-mobile uk":            "EE",
    "t-mobile":               "T-Mobile",
    "3":                      "Three",
    "hutchison 3g uk":        "Three",
    "o2 (uk)":                "O2",
    "o2 - uk":                "O2",
    "ee / orange":            "EE",
    "tata docomo":            "Tata Docomo",
    "docomo":                 "NTT Docomo",
    "ntt docomo":             "NTT Docomo",
    "kddi":                   "KDDI",
    "au":                     "KDDI",
    "au by kddi":             "KDDI",
    "softbank":               "SoftBank",
    "softbank mobile":        "SoftBank",
    "china mobile":           "China Mobile",
    "china unicom":           "China Unicom",
    "china telecom":          "China Telecom",
    "sk telecom":             "SK Telecom",
    "lg u+":                  "LG U+",
    "lg uplus":               "LG U+",
    "lg telecom":             "LG U+",
    "etisalat":               "Etisalat",
    "mobily":                 "Mobily",
    "zain sa":                "Zain",
    "al jawal (stc)":         "STC",
    "stc":                    "STC",
    "grameenphone":           "Grameenphone",
    "telenor":                "Telenor",
    "tata teleservices":      "Tata Docomo",
}


def clean_dataset_brand(brand: str) -> str:
    """
    Take a brand string as stored in the bundled dataset and return a
    human-friendly canonical name. Falls back to the original brand if
    no alias is found.
    """
    if not brand:
        return ""
    key = brand.lower().strip()
    if key in DATASET_BRAND_ALIASES:
        return DATASET_BRAND_ALIASES[key]
    # Substring fallback
    for alias, canonical in DATASET_BRAND_ALIASES.items():
        if alias in key:
            return canonical
    return brand
