"""
examples.py
===========

A handful of well-known MSISDNs to use for quick smoke tests.
All are public / well-known sample numbers; do NOT use them as live
subscribers.

Author: pentesterclub
"""

# Indian mobile (Airtel)
INDIAN_AIRTEL    = "+919876543210"

# Indian mobile (Jio)
INDIAN_JIO       = "+919999999999"

# US number (San Francisco)
US_SF            = "+14155552671"

# UK mobile (O2)
UK_O2            = "+447911123456"

# UK Vodafone
UK_VODAFONE      = "+447700900123"

# Germany (T-Mobile)
DE_TMOBILE       = "+4915112345678"

# France (Orange)
FR_ORANGE        = "+33612345678"

# China (China Mobile)
CN_MOBILE        = "+8613800138000"

# Japan (NTT Docomo)
JP_DOCOMO        = "+819012345678"

# South Korea (SK Telecom)
KR_SKT           = "+821012345678"

# Brazil (Vivo)
BR_VIVO          = "+5511991234567"

# Australia (Telstra)
AU_TELSTRA       = "+61412345678"

# Singapore (SingTel)
SG_SINGTEL       = "+6581234567"

# UAE (Etisalat)
AE_ETISALAT      = "+971501234567"

# Bangladesh (Grameenphone)
BD_GP            = "+8801712345678"

# Mexico (Telcel)
MX_TELCEL        = "+525555555555"

# South Africa (Vodacom)
ZA_VODACOM       = "+27821234567"


SAMPLE_SET = [
    INDIAN_AIRTEL,
    INDIAN_JIO,
    US_SF,
    UK_O2,
    UK_VODAFONE,
    DE_TMOBILE,
    FR_ORANGE,
    CN_MOBILE,
    JP_DOCOMO,
    BR_VIVO,
    AU_TELSTRA,
    SG_SINGTEL,
    AE_ETISALAT,
    BD_GP,
    MX_TELCEL,
    ZA_VODACOM,
]


if __name__ == "__main__":
    from decoder import decode, __author__, __version__
    import json
    print(f"MSISDN Decoder v{__version__} — built by {__author__}")
    print()
    for n in SAMPLE_SET:
        print(f"--- {n} ---")
        r = decode(n)
        r2 = {k: v for k, v in r.items() if k != "warning"}
        print(json.dumps(r2, indent=2, ensure_ascii=False))
        print()
