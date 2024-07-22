#!/usr/bin/python3

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

import datetime


class Screen:
    """ this is a class to make a screen for the console"""
    def __init__(self):
        self.console = Console(color_system="truecolor")
        super().__init__()

    def make_layout(self) -> Layout:
        """ make a layout for the console"""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=7)
        )
        layout["main"].split_row(
            Layout(name="side"),
            Layout(name="telegram_table", minimum_size=60),
        )
        layout["side"].split(Layout(name="usage"), Layout(name="month_peak", size=19))
        layout["footer"].split_row(
            Layout(name="log"),
            Layout(name="quarter_peak"),
        )
        layout["usage"].split(Layout(name="rate", size=5), Layout(name="usage_table"))
        return layout

    def make_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center")
        grid.add_row("Digital Meter - P1 Telegram",
                     f"Version 1.0 {self.ts_str(self.cur_time) if hasattr(self, 'cur_time') else 'no time yet'}")
        return Panel(grid, style="white on blue")

    def make_telegram_table(self) -> Table:
        table = Table(show_lines=False, expand=True)
        table.add_column("Obis", justify="left", style="cyan", no_wrap=True)
        table.add_column("Thing", justify="left", style="magenta")
        table.add_column("Description", justify="left", style="green")
        table.add_column("Value", justify="left", style="blue")
        for row in self.p1_table:
            table.add_row(*row)
        return table

    def make_rate_table(self) -> Table:
        table = Table(show_lines=False, expand=True, box=None)
        for rate_c in self._rate_columns():
            # make the column for the rate table cyan if it is the current rate else magenta
            hit = True if "kWh" not in rate_c else \
                ((self.cur_rate == 1) and ("Day" in rate_c)) or ((self.cur_rate == 2) and ("Night" in rate_c))
            table.add_column(rate_c, justify="center", style="magenta" if hit else "cyan")
        for sign in ["+", "-"]:
            rend = []
            for tpe in ["Electricity", "Gas", "Water"]:
                if sign not in self.rates_dct[tpe]:
                    rend.append("")
                elif isinstance(self.rates_dct[tpe][sign], dict):
                    rend.append(f"{self.rates_dct[tpe][sign]['Day']:.2f}")
                    rend.append(f"{self.rates_dct[tpe][sign]['Night']:.2f}")
                else:
                    rend.append(f"{self.rates_dct[tpe][sign]:.2f}")
            table.add_row(sign, *rend)
        return table

    def make_usage_table(self) -> Table:
        """ beware, styling is contingent on the text in the first column, such as "Day" or "Night" or "Total" """
        table = Table(show_lines=False, expand=True)
        table.add_column("Usage/Cost", justify="left", style="magenta")

        for x in self._usage_columns():
            # change the header text to the day of the week if it is a past day
            txt = x if "Day-" not in x else (self.data["cur_time"]-datetime.timedelta(days=int(x.split("-")[1]))).strftime("%A")
            table.add_column(txt, justify="right", style="magenta" if x == "Today" else "green")

        for pos, line in enumerate(self._usage_rows()):
            # highlight day or night usage depending on the current rate
            hit = (self.cur_rate == 1 and "Day" in line or self.cur_rate == 2 and "Night" in line)
            table.add_row(line, *[f"{self.usage[x][pos]:.2f}" for x in self._usage_columns()],
                          style="green" if hit else "blue", end_section=True if "Σ" in line else False)
            if line == "Σ € kWh":
                # add the 2 quarter peak lines
                p, dp = [], []
                for x in self._usage_columns():
                    p.append(f"{self.day_peak[x][0]:.2f}" if "day" in x.lower() else "-")
                    dp.append(f"{self.day_peak[x][1].strftime('%H:%M')}" if "day" in x.lower() and self.day_peak[x][1] else "-")
                table.add_row("Day Peak kW", *p, style="green"),
                table.add_row("¼ @ hh:mm",   *dp, style="green", end_section=True)
        return table

    def make_log_table(self) -> Table:
        table = Table.grid()
        table.add_column(justify="left", style="cyan")
        table.add_column(justify="left", style="magenta")
        table.add_column(justify="left", style="magenta")
        for row in sorted(self.log, reverse=True):
            table.add_row(row, " ", self.log[row])
        return table


    def make_month_peak_table(self) -> Table:
        table = Table(show_lines=False, expand=True)
        table.add_column("Month", justify="left", style="cyan", no_wrap=True)
        table.add_column("When", justify="left", style="magenta")
        table.add_column("Peak", justify="left", style="green")
        table.add_column("Unit", justify="left", style="green")
        # show current month peak first
        table.add_row("Current Month", self.ts_str(self.month_peak["time"]), f"{self.month_peak['value']:06.3f}",
                      self.month_peak["unit"])
        for m in sorted(getattr(self, "months_peak_past", {}).get("table", {}), reverse=True):
            it = self.months_peak_past["table"][m]
            table.add_row(self.ts_str(m), self.ts_str(it[0]), *it[1:])
        return table

    def make_quarter_peak(self) -> Progress:
        grid = Table.grid(expand=True)
        grid.add_column(justify="centre")
        quarter_progress = Progress("{task.description}",
                                    SpinnerColumn(), BarColumn(),
                                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))
        cq = quarter_progress.add_task("Clock Quarter", total=self.clock_todo)
        quarter_progress.update(cq, completed=self.clock_done)
        grid.add_row(quarter_progress)
        grid.add_row(f"Peak -> Till Now {self.quarter_peak:.3f} kW, Forecast Quarter: {self.peak_forecast:.3f} kW")
        grid.add_row(f"Month Peak: {self.month_peak['value']:.3f} kW <> Quarter Forecast: {self.peak_forecast:.3f} kW",
                         style=self.peak_gap_style)
        grid.add_row(f"GAP: {self.peak_gap:.3f} kW at rate {self.cur_rate}",
                         style=self.peak_gap_style)
        return grid


    def update_layout(self, layout):
        """ update the layout with the data from the meter"""
        layout["header"].update(self.make_header())
        layout["telegram_table"].update(Panel(self.make_telegram_table(), title="Telegram"))
        layout["month_peak"].update(Panel(self.make_month_peak_table(), title="Months Peak"))
        layout["log"].update(Panel(self.make_log_table(), title="Log"))
        layout["usage_table"].update(Panel(self.make_usage_table(),
                                           title=f"Usage since {self.ts_str(self.data['start_time'])}"))
        layout["rate"].update(Panel(self.make_rate_table(), title="Rate"))
        layout["quarter_peak"].update(Panel(self.make_quarter_peak(),
                                            title="Quarters Peak", border_style=self.peak_gap_style))
