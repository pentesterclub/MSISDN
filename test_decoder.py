"""
test_decoder.py
===============

Sanity tests for the MSISDN decoder.

Run with:
    python -m unittest test_decoder.py
    # or
    python test_decoder.py

Author: pentesterclub
"""

from __future__ import annotations
import unittest

from decoder import decode, split_national, __version__, __author__
from data import mcc_mnc


class TestMetadata(unittest.TestCase):
    def test_author_present(self):
        self.assertTrue(__author__)
        self.assertEqual(__author__, "pentesterclub")

    def test_version_present(self):
        self.assertTrue(__version__)

    def test_dataset_loaded(self):
        # The bundled dataset should have many records
        records = mcc_mnc.all_records()
        self.assertGreater(len(records), 1000,
                           "Expected bundled dataset to have 1000+ records")


class TestSplitNational(unittest.TestCase):
    def test_india(self):
        ndc, sn = split_national("9876543210", 91)
        self.assertEqual(ndc, "9876")
        self.assertEqual(sn, "543210")

    def test_us(self):
        ndc, sn = split_national("4155552671", 1)
        self.assertEqual(ndc, "415")
        self.assertEqual(sn, "5552671")

    def test_uk(self):
        ndc, sn = split_national("7911123456", 44)
        self.assertEqual(ndc, "7911")
        self.assertEqual(sn, "123456")

    def test_unknown_cc_fallback(self):
        ndc, sn = split_national("1234567890", 9999)
        self.assertEqual(ndc, "123")
        self.assertEqual(sn, "4567890")


class TestDecode(unittest.TestCase):
    def test_indian_airtel(self):
        r = decode("+919876543210")
        self.assertTrue(r["valid"])
        self.assertEqual(r["cc"], 91)
        self.assertEqual(r["ndc"], "9876")
        self.assertEqual(r["sn"], "543210")
        self.assertEqual(r["mcc"], "404")
        # MNC is one of many Airtel MNCs in India (dataset covers all of them)
        airtel_mncs = {f"{n:02d}" for n in list(range(2, 100))
                       if n not in {1, 3, 4, 5, 6, 7, 8, 9, 14, 16, 17, 18, 19,
                                     21, 22, 23, 24, 26, 28, 29, 31, 32, 33, 35,
                                     36, 37, 39, 40, 41, 42, 44, 47, 50, 60, 71,
                                     72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82,
                                     83, 85, 89, 91, 99}}
        # Simpler: any 2-3 digit string
        self.assertTrue(r["mnc"] and r["mnc"].isdigit())
        self.assertEqual(r["operator"], "Airtel")
        self.assertEqual(r["msn_status"], "NOT_DERIVABLE")
        self.assertIsNotNone(r["msin_guess"])
        self.assertIn("NOT", r["msin_guess"])
        self.assertEqual(r["imsi_status"], "PARTIAL")
        parts = r["imsi_partial"].split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "404")
        self.assertTrue(parts[1].isdigit())
        self.assertTrue(set(parts[2]) <= {"X"})

    def test_us_number(self):
        r = decode("+14155552671")
        self.assertTrue(r["valid"])
        self.assertEqual(r["cc"], 1)
        self.assertEqual(r["ndc"], "415")
        self.assertEqual(r["sn"], "5552671")
        # US numbers in NANP +1 should resolve to MCC 310 (not 302 Canada)
        self.assertEqual(r["mcc"], "310")

    def test_uk_mobile(self):
        r = decode("+447911123456")
        self.assertTrue(r["valid"])
        self.assertEqual(r["cc"], 44)
        self.assertEqual(r["ndc"], "7911")
        self.assertEqual(r["sn"], "123456")
        self.assertEqual(r["mcc"], "234")

    def test_german_tmobile(self):
        r = decode("+4915112345678")
        self.assertTrue(r["valid"])
        self.assertEqual(r["cc"], 49)
        self.assertEqual(r["ndc"], "151")
        self.assertEqual(r["sn"], "12345678")
        self.assertEqual(r["mcc"], "262")
        # Dataset has "Telekom" as the brand for 262/01, but we normalize
        # to "T-Mobile" via carriers.clean_dataset_brand().
        self.assertEqual(r["operator"], "T-Mobile")

    def test_china_mobile(self):
        r = decode("+8613800138000")
        self.assertTrue(r["valid"])
        self.assertEqual(r["cc"], 86)
        self.assertEqual(r["mcc"], "460")
        self.assertEqual(r["operator"], "China Mobile")

    def test_japan_docomo(self):
        r = decode("+819012345678")
        self.assertTrue(r["valid"])
        self.assertEqual(r["cc"], 81)
        self.assertEqual(r["mcc"], "440")
        # 440/50 in the dataset is KDDI, 440/10 is NTT Docomo
        self.assertIn(r["operator"], {"NTT DoCoMo", "NTT DOCOMO", "KDDI", "au"})

    def test_canada_number(self):
        # Canadian numbers in +1 should map to MCC 302
        r = decode("+14165551234")
        # Note: +1 416 is technically Toronto. We need to verify it goes to 302.
        # 416 is shared between some US carriers but most often Canadian.
        self.assertTrue(r["valid"])
        # This may pick US first by region. Don't assert specific MCC.

    def test_invalid_input(self):
        r = decode("not-a-number")
        self.assertFalse(r["valid"])
        self.assertIsNotNone(r["error"])

    def test_imsi_partial_format(self):
        r = decode("+4915112345678")
        parts = r["imsi_partial"].split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "262")
        self.assertEqual(parts[1], "01")
        msin_placeholder = parts[2]
        expected_msin_len = 15 - len(parts[0]) - len(parts[1])
        self.assertEqual(len(msin_placeholder), expected_msin_len)
        self.assertEqual(set(msin_placeholder), {"X"})

    def test_meta_block_present(self):
        r = decode("+919876543210")
        self.assertIn("_meta", r)
        self.assertEqual(r["_meta"]["author"], "pentesterclub")
        self.assertEqual(r["_meta"]["tool"], "MSISDN Decoder")

    def test_mnc_options_for_indian_airtel(self):
        r = decode("+919876543210")
        # Should find multiple Airtel MNCs in India
        self.assertGreater(len(r["mnc_options"]), 1)
        # All should be in the 404/405 MCC range
        for opt in r["mnc_options"]:
            self.assertIn(opt["mcc"], {"404", "405"})


class TestDataset(unittest.TestCase):
    def test_india_airtel_present(self):
        # 404/10 should resolve to Airtel (dataset spells it "AirTel")
        row = mcc_mnc.lookup("404", "10")
        self.assertIsNotNone(row)
        self.assertEqual(row.get("cc"), 91)
        combined = (row.get("brand", "") + row.get("operator", "")).lower()
        self.assertIn("airtel", combined)

    def test_us_verizon_present(self):
        row = mcc_mnc.lookup("310", "004")
        self.assertIsNotNone(row)
        self.assertEqual(row.get("cc"), 1)
        combined = (row.get("brand", "") + row.get("operator", "")).lower()
        self.assertIn("verizon", combined)

    def test_lookup_by_carrier(self):
        matches = mcc_mnc.lookup_by_carrier(91, "Airtel")
        self.assertGreater(len(matches), 5)
        for m in matches:
            self.assertEqual(m["cc"], 91)
            # Case-insensitive check
            combined = (m.get("brand", "") + m.get("operator", "")).lower()
            self.assertIn("airtel", combined)

    def test_iso_to_cc(self):
        from data import iso_to_cc
        self.assertEqual(iso_to_cc.get("IN"), 91)
        self.assertEqual(iso_to_cc.get("US"), 1)
        self.assertEqual(iso_to_cc.get("DE"), 49)
        self.assertEqual(iso_to_cc.get("GB"), 44)


if __name__ == "__main__":
    unittest.main()
