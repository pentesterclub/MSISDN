#!/usr/bin/env python3
"""
msisdn_tool.py
==============

CLI entry point for the MSISDN Decoder.

USAGE
-----
    python msisdn_tool.py <MSISDN>          # pretty terminal output
    python msisdn_tool.py <MSISDN> --json   # raw JSON output
    python msisdn_tool.py --demo            # run against the built-in demo set
    python msisdn_tool.py --version         # print version and exit
    python msisdn_tool.py --stats           # show bundled dataset stats

Author:  pentesterclub
Version: 1.1.0
"""

from __future__ import annotations
import sys
import json
import argparse

from decoder import decode, __version__, __author__
from formatter import format_result


DEMO_NUMBERS = [
    "+14155552671",      # USA — San Francisco
    "+447911123456",     # UK — mobile
    "+919876543210",     # India — mobile
    "+4915112345678",    # Germany — T-Mobile
    "+33612345678",      # France — mobile
    "+8613800138000",    # China — mobile
    "+819012345678",     # Japan — mobile
    "+5511991234567",    # Brazil — São Paulo
    "+61412345678",      # Australia — mobile
    "+6581234567",       # Singapore — mobile
    "+8801712345678",    # Bangladesh — mobile
    "+971501234567",     # UAE — mobile
    "+12425551234",      # Caribbean
    "+12427891234",      # Caribbean
    "+525555555555",     # Mexico — mobile
    "+27821234567",      # South Africa — mobile
]


BANNER = r"""
 _   _ ___  ___  _  _  ___   ___   ___  ___   ___  ___  ___   ___   ___  __  __
| \ | | _ \/ _ \| \| |/ __| |   \ | __|| \ | | _ \/ __|| __|| \   /_\ |  \/  |
| .` |   / (_) | .` | (_ | | |) || _| | .` |   / (_ || _| | |) | / _ \| |\/| |
|_|\_|_|_\\___/|_|\_|\___| |___/ |___||_|\_|_|_\\___||___||___//_/ \_\_|  |_|

                      p e n t e s t e r c l u b
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="msisdn_tool",
        description=f"{BANNER}\nMSISDN → CC / NDC / SN + best-effort MCC / MNC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("msisdn", nargs="?", help="MSISDN in E.164 format, e.g. +14155552671")
    p.add_argument("--json",   action="store_true", help="Output raw JSON instead of pretty table")
    p.add_argument("--demo",   action="store_true", help="Run against the built-in demo set")
    p.add_argument("--version", action="store_true", help="Print version info and exit")
    p.add_argument("--stats",  action="store_true", help="Show bundled dataset statistics")
    return p.parse_args(argv)


def print_banner() -> None:
    from rich.console import Console
    from rich.text import Text
    c = Console()
    c.print(Text(BANNER, style="bold cyan"))


def print_version() -> None:
    print(f"msisdn_tool v{__version__}")
    print(f"Author: {__author__}")


def print_stats() -> None:
    import mcc_mnc
    from rich.console import Console
    from rich.table import Table

    table = Table(title=f"Bundled MCC-MNC Dataset — built by {__author__}",
                  show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value",  style="white")

    records = mcc_mnc.all_records()
    countries = sorted({r["country"] for r in records if r.get("country")})
    mccs      = sorted({r["mcc"] for r in records if r.get("mcc")})
    operators = sorted({r.get("brand") or r.get("operator", "") for r in records})
    operational = sum(1 for r in records if r.get("status") == "Operational")

    table.add_row("Total records",       str(len(records)))
    table.add_row("Total countries",     str(len(countries)))
    table.add_row("Total MCCs",          str(len(mccs)))
    table.add_row("Total operators",     str(len(operators)))
    table.add_row("Operational records", str(operational))

    Console().print(table)


def run_one(msisdn: str, as_json: bool) -> int:
    if not as_json:
        print_banner()
    result = decode(msisdn)
    if as_json:
        r2 = {k: v for k, v in result.items() if k != "warning"}
        print(json.dumps(r2, indent=2, ensure_ascii=False))
    else:
        format_result(result)
    return 0 if result.get("valid") else 2


def run_demo(as_json: bool) -> int:
    from rich.console import Console
    console = Console()
    if not as_json:
        print_banner()
    for n in DEMO_NUMBERS:
        if not as_json:
            console.rule(f"[bold cyan]{n}[/bold cyan]")
        result = decode(n)
        if as_json:
            r2 = {k: v for k, v in result.items() if k != "warning"}
            print(json.dumps(r2, indent=2, ensure_ascii=False))
            print("---")
        else:
            console.print(
                f"  CC=[cyan]{result['cc']}[/cyan]  "
                f"NDC=[cyan]{result['ndc']}[/cyan]  "
                f"SN=[cyan]{result['sn']}[/cyan]  →  "
                f"MCC=[green]{result['mcc']}[/green]  "
                f"MNC=[green]{result['mnc']}[/green]  "
                f"Op=[green]{result['operator']}[/green]  "
                f"MSIN=[red]NOT DERIVABLE[/red]"
            )
    if not as_json:
        console.rule(f"[bold]{__author__} — done[/bold]")
    return 0


def main() -> int:
    args = parse_args(sys.argv[1:])

    if args.version:
        print_version()
        return 0
    if args.stats:
        print_banner()
        print_version()
        print_stats()
        return 0
    if args.demo or (not args.msisdn and not args.json):
        return run_demo(args.json)

    return run_one(args.msisdn, args.json)


if __name__ == "__main__":
    sys.exit(main())
