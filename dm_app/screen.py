#!/usr/bin/python3

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn


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
            table.add_column(x, justify="right", style="cyan")
        for pos, line in enumerate(self._usage_rows()):
            # highlight day or night usage depending on the current rate
            hit = (self.cur_rate == 1 and "Day" in line or self.cur_rate == 2 and "Night" in line)
            table.add_row(line, *[f"{self.usage[x][pos]:.2f}" for x in self._usage_columns()],
                          style="green" if hit else "blue", end_section=True if "Σ" in line else False)
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
        clock_todo = 15*60  # seconds in a quarter
        quarter_progress = Progress("{task.description}",
                                    SpinnerColumn(), BarColumn(),
                                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))
        cq = quarter_progress.add_task("Clock Quarter", total=clock_todo)
        pb = quarter_progress.add_task("Peak Buildup", total=100)
        pf = quarter_progress.add_task("Peak Forecast", total=100)
        clock_done = (self.cur_time.minute % 15) * 60 + self.cur_time.second  # seconds in the current quarter
        quarter_progress.update(cq, completed=clock_done)
        quarter_progress.update(pb, total=self.quarter_peak * clock_todo / (clock_todo - clock_done),
                                    completed=self.quarter_peak)
        return quarter_progress


    def update_layout(self, layout):
        """ update the layout with the data from the meter"""
        layout["header"].update(self.make_header())
        layout["telegram_table"].update(Panel(self.make_telegram_table(), title="Telegram"))
        layout["month_peak"].update(Panel(self.make_month_peak_table(), title="Months Peak"))
        layout["log"].update(Panel(self.make_log_table(), title="Log"))
        layout["usage_table"].update(Panel(self.make_usage_table(), title="Usage"))
        layout["rate"].update(Panel(self.make_rate_table(), title="Rate"))
        layout["quarter_peak"].update(Panel(self.make_quarter_peak(), title="Quarters Peak", border_style="green"))
