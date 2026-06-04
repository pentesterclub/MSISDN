# MSISDN Decoder Tool

**Built by [pentesterclub](https://pentesterclub.com)**

Decode an MSISDN (phone number) into its CC / NDC / SN parts and produce a
best-effort guess at the operator's MCC / MNC. The full global MCC-MNC
dataset is bundled (2700+ records, 230+ countries, sourced from the
public `mcc-mnc-list` repository which mirrors the live ITU-T E.212
assignments).

```
  Input:   +919876543210

  MSISDN:  CC=91   NDC=9876   SN=543210
  IMSI:    MCC=404 MNC=10    MSIN = NOT DERIVABLE
  Op:      Airtel (Bharti Airtel Limited)
```

## ⚠ Important — read this first

| Field | Derivable from MSISDN? | Why |
|---|---|---|
| CC (Country Code) | ✅ Yes | Part of the number itself |
| NDC + SN | ✅ Yes | Country-specific split |
| MCC | ✅ Best match | CC → MCC mapping (bundled global dataset) |
| MNC | ✅ Best match | MCC + carrier name → MNC table (bundled) |
| **MSIN** | ❌ **No** | Lives in operator's HLR/HSS only |

**MSIN cannot be recovered from an MSISDN.** It is assigned by the
operator and the mapping is held in their subscriber database
(HLR / HSS). The tool marks MSIN as `NOT_DERIVABLE` in the output
rather than fabricating a value.

## Project structure

```
msisdn_tool/
├── README.md                 # this file
├── requirements.txt          # pip dependencies
├── msisdn_tool.py            # CLI entry point
├── decoder.py                # core decode() logic
├── formatter.py              # pretty terminal output (rich)
├── examples.py               # sample MSISDNs to try
├── test_decoder.py           # unit tests
├── data/
│   ├── __init__.py
│   ├── mcc_mnc_full.json     # bundled global MCC-MNC dataset (2700+ records)
│   ├── mcc_mnc.py            # loader + lookup API
│   ├── carriers.py           # carrier-name normalization
│   └── iso_to_cc.py          # ISO 3166-1 alpha-2 -> E.164 CC
```

## Installation

```bash
cd msisdn_tool
pip install -r requirements.txt
```

The tool ships with the full global MCC-MNC dataset already bundled as
`data/mcc_mnc_full.json`, so it works offline out of the box. No
runtime download required.

## Usage

### One number, pretty output

```bash
python msisdn_tool.py "+919876543210"
```

### One number, raw JSON

```bash
python msisdn_tool.py "+919876543210" --json
```

### Demo batch (16 built-in samples)

```bash
python msisdn_tool.py --demo
```

### Dataset statistics

```bash
python msisdn_tool.py --stats
```

### Version info

```bash
python msisdn_tool.py --version
```

### Use as a library

```python
from decoder import decode

result = decode("+919876543210")
print(result["cc"])         # 91
print(result["ndc"])        # 9876
print(result["sn"])         # 543210
print(result["mcc"])        # 404
print(result["mnc"])        # 10
print(result["operator"])   # Airtel
print(result["msin_guess"]) # NOT derivable
```

## Sample output

```
╔══════════════════════════════════════════════════════════════╗
║                  MSISDN DECODER RESULT                        ║
║              v1.1.0 · built by pentesterclub                  ║
╠══════════════════════════════════════════════════════════════╣
║ MSISDN (input):     +919876543210                            ║
║ E.164 normalized:   +919876543210                            ║
║ Valid E.164:        ✓ Yes                                    ║
╠══════════════════════════════════════════════════════════════╣
║ MSISDN Components                                            ║
║   CC:        91       Country Code (E.164)                   ║
║   NDC:       9876     National Destination Code              ║
║   SN:        543210   Subscriber Number                      ║
║   Country:   India    Detected country                       ║
║   Region:    Maharashtra                                     ║
╠══════════════════════════════════════════════════════════════╣
║ IMSI Components (best-effort)                                ║
║   MCC:       404      Mobile Country Code                    ║
║   MNC:       10       Mobile Network Code                    ║
║   Operator:  Airtel                                          ║
║   MSIN:      NOT DERIVABLE  (operator-internal)              ║
╠══════════════════════════════════════════════════════════════╣
║ IMSI structure: 404-10-XXXXXXXXX                             ║
╚══════════════════════════════════════════════════════════════╝
                          — built by pentesterclub · v1.1.0
```

## Running tests

```bash
python -m unittest test_decoder.py -v
```

14+ tests covering:

- NDC/SN split rules for major countries
- MSISDN → CC/MCC/MNC decode
- Operator / carrier name resolution
- Region disambiguation (US vs Canada in +1)
- Bundled dataset integrity
- Author / version metadata

## Updating the bundled dataset

The bundled `data/mcc_mnc_full.json` is sourced from the public
`mcc-mnc-list` repository, which mirrors the live ITU-T E.212
assignments. To refresh it:

```bash
curl -sL "https://raw.githubusercontent.com/ppai-plivo/mcc-mnc-list/master/mcc-mnc-list.json" \
     -o data/mcc_mnc_full.json
python -m unittest test_decoder.py
```

## License & ethics

This tool is for educational, defensive, and engineering purposes only.
Do not use it to:

- Track or identify individuals without consent
- Bypass operator authentication
- Process personal data without a legal basis

The bundled MSISDN samples are well-known public test numbers and must
not be used as live subscribers.

---

**Author:** pentesterclub · **Version:** 1.1.0
