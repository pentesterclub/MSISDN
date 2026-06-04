"""
formatter.py
============

Pretty-print the decode() result to the terminal using `rich`.

Author: pentesterclub
"""

from __future__ import annotations
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from decoder import __author__, __version__, __tool_name__


def format_result(result: dict) -> None:
    """Render the decode() result to a colorful terminal output."""
    console = Console()

    if result.get("error"):
        console.print(Panel(
            f"[red bold]Error parsing MSISDN:[/red bold]\n{result['error']}",
            title=f"{__tool_name__} — {__author__}",
            border_style="red",
        ))
        return

    # ---- Title panel ----
    from rich.align import Align
    title = Text()
    title.append("MSISDN DECODER RESULT", style="bold cyan")
    title.append(f"\nv{__version__} · built by {__author__}", style="dim")
    console.print(Panel(Align.center(title), box=box.DOUBLE, border_style="cyan"))

    # ---- Input ----
    input_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    input_table.add_column(style="bold")
    input_table.add_column()
    valid_mark = "[green]✓ Yes[/green]" if result["valid"] else "[red]✗ No[/red]"
    input_table.add_row("MSISDN (input):",      f"[white]{result['input']}[/white]")
    input_table.add_row("E.164 normalized:",    f"[white]{result['e164_format']}[/white]")
    input_table.add_row("Valid E.164:",         valid_mark)
    console.print(input_table)

    # ---- MSISDN components ----
    msisdn_table = Table(
        title="[bold]MSISDN Components[/bold]",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold magenta",
    )
    msisdn_table.add_column("Field", style="bold cyan", no_wrap=True)
    msisdn_table.add_column("Value", style="white")
    msisdn_table.add_column("Description", style="dim")
    msisdn_table.add_row("CC",       str(result["cc"]),     "Country Code (E.164)")
    msisdn_table.add_row("NDC",      str(result["ndc"]),    "National Destination Code")
    msisdn_table.add_row("SN",       str(result["sn"]),     "Subscriber Number")
    msisdn_table.add_row("Country",  str(result["country"]),"Detected country")
    msisdn_table.add_row("Region",   str(result["region"]) or "—", "Geographic region / city")
    console.print(msisdn_table)

    # ---- IMSI components ----
    imsi_table = Table(
        title="[bold]IMSI Components (best-effort, see warning)[/bold]",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold magenta",
    )
    imsi_table.add_column("Field",      style="bold cyan", no_wrap=True)
    imsi_table.add_column("Value",      style="white")
    imsi_table.add_column("Description", style="dim")
    imsi_table.add_row("MCC",          str(result["mcc"])     or "—",  "Mobile Country Code")
    imsi_table.add_row("MNC",          str(result["mnc"])     or "—",  "Mobile Network Code")
    imsi_table.add_row("Operator",     str(result["operator"]) or "—", "Carrier (best match)")

    msin_value = result["msin_guess"] or "—"
    imsi_table.add_row("MSIN",         msin_value,                     "[red]NOT DERIVABLE[/red]")
    console.print(imsi_table)

    # ---- IMSI structure template ----
    if result.get("imsi_partial"):
        imsi_text = Text()
        imsi_text.append("IMSI structure: ", style="bold yellow")
        imsi_text.append(result["imsi_partial"], style="white")
        imsi_text.append("   (", style="dim")
        imsi_text.append("MCC", style="cyan")
        imsi_text.append(" - ", style="dim")
        imsi_text.append("MNC", style="cyan")
        imsi_text.append(" - ", style="dim")
        imsi_text.append("MSIN", style="red")
        imsi_text.append(" placeholder)", style="dim")
        console.print(Panel(imsi_text, border_style="yellow"))

    # ---- MNC options ----
    options = result.get("mnc_options") or []
    if len(options) > 1:
        opt_table = Table(
            title=f"[bold]MNC candidates for carrier '{result['carrier_canonical']}'[/bold]",
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style="bold magenta",
        )
        opt_table.add_column("MCC",      style="cyan")
        opt_table.add_column("MNC",      style="cyan")
        opt_table.add_column("Operator", style="white")
        opt_table.add_column("Status",   style="dim")
        opt_table.add_column("Bands",    style="dim")
        for row in options:
            opt_table.add_row(
                row["mcc"], row["mnc"],
                row.get("operator") or "—",
                row.get("status") or "—",
                row.get("bands") or "—",
            )
        console.print(opt_table)

    # ---- Carrier info ----
    carrier_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    carrier_table.add_column(style="bold")
    carrier_table.add_column()
    carrier_table.add_row("Carrier (libphonenumber):", str(result["carrier_raw"]) or "—")
    carrier_table.add_row("Carrier (normalized):",     str(result["carrier_canonical"]) or "—")
    if result.get("mcc_candidates"):
        mccs = ", ".join(result["mcc_candidates"][:6])
        if len(result["mcc_candidates"]) > 6:
            mccs += f", … (+{len(result['mcc_candidates']) - 6} more)"
        carrier_table.add_row("MCC candidates (from CC):", mccs)
    console.print(carrier_table)

    # ---- Warning ----
    console.print(Panel(
        f"[bold yellow]⚠ {result['warning']}[/bold yellow]",
        border_style="yellow",
    ))

    # ---- Footer ----
    console.print(f"[dim]— built by {__author__} · v{__version__}[/dim]")
