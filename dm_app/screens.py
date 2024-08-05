#!/usr/bin/python3

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

import datetime


class Screens:
    """ this is a class to make a screen for the console"""
    def __init__(self, *args, **kwargs):
        self.console = Console(color_system="truecolor")
        super().__init__(*args, **kwargs)

    def make_layout(self) -> Layout:
        """ return layout of the console"""
        layout = Layout(name="root")
        layout.split(Layout(name="header", size=3),
                     Layout(name="main"))
        layout["main"].split_row(Layout(name="left_side"), Layout(name="telegram", minimum_size=60))
        layout["left_side"].split(Layout(name="rate", size=5),
                                  Layout(name="usage"),
                                  Layout(name="month_peak", size=19),
                                  Layout(name="quarter_peak", size=7))
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
            line_1st = "   (R1)" if "day" in line.lower() else " (R2)" if "night" in line.lower() else ""
            table.add_row(f"{line}{line_1st}", *[f"{self.usage[x][pos]:.2f}" for x in self._usage_columns()],
                          style="green" if hit else "blue", end_section=True if "Σ" in line else False)
            # insert some lines at the right point
            match line:
                case "m3 Gas":  # if cnv for gas is in the rates_dct, convert the m3 to the unit in the rates_dct
                    if "cnv" in self.rates_dct["Gas"]:
                        cnv_str, cnv = self.rates_dct["Gas"]["cnv"]
                        table.add_row(line.replace("m3", cnv_str),
                                      *[f"{self.usage[x][pos]*cnv:.2f}" for x in self._usage_columns()], style="blue")
                case "Σ € kWh":  # add the 2 quarter peak lines when a day in the column to mark a day peak
                    p, dp = [], []
                    for x in self._usage_columns():
                        # make the columns for the day_peak "-" if it is not a day peak or when not time set
                        if "day" in x.lower() and (_when := self.day_peak[x][1]):
                            _peak, _when = f"{self.day_peak[x][0]:.2f}", f"{_when.strftime('%H:%M')}"
                        else:
                            _peak, _when = "-", "-"
                        p.append(_peak)
                        dp.append(_when)
                    table.add_row("Peak kW", *p, style="blue"),
                    table.add_row("¼ @ hh:mm",   *dp, style="blue", end_section=True)
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
        layout["telegram"].update(Panel(self.make_telegram_table(), title="Telegram"))
        layout["month_peak"].update(Panel(self.make_month_peak_table(), title="Months Peak"))
        # layout["log"].update(Panel(self.make_log_table(), title="Log"))
        layout["usage"].update(Panel(self.make_usage_table(),
                                           title=f"Usage since {self.ts_str(self.data['start_time'])}"))
        layout["rate"].update(Panel(self.make_rate_table(),
                                    title="Rate => [magenta]1:day 07:00 22:00, [blue]2:night 22:00 07:00 + weekend + holidays"))
        layout["quarter_peak"].update(Panel(self.make_quarter_peak(),
                                            title="Quarters Peak", border_style=self.peak_gap_style))
