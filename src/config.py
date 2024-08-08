#!/usr/bin/python3
from collections import namedtuple

pickle_file = "data.pickle"
dir_history = "./history/"
log_name = "log_info"
log_file = f"{log_name}.log"

obis_el = namedtuple('OBIS', ['th_n', 'class_id', 'description'])

# OBIS codes for P1 telegram from eMUCS-P1 version 2.1.1

obiscodes = {
    "0-0:96.1.4": obis_el("version", 1, "Version major.minor (current is 50221)"),
    "0-0:1.0.0": obis_el("time_now", 8, "Timestamp current time"),
    "0-0:96.13.0": obis_el("message", 1, "Text Message, max 1024 chars"),
    "0-0:96.14.0": obis_el("active_rate", 1, "Current rate (1=day,2=night)"),
    "1-0:1.8.1": obis_el("kwH_day_plus", 3, "Rate 1 (day) - total consumption"),
    "1-0:1.8.2": obis_el("kwH_night_plus", 3, "Rate 2 (night) - total consumption"),
    "1-0:2.8.1": obis_el("kwH_day_min", 3, "Rate 1 (day) - total production"),
    "1-0:2.8.2": obis_el("kwH_night_min", 3, "Rate 2 (night) - total production"),
    "1-0:1.7.0": obis_el("kW_plus", 3, "All phases current consumption"),
    "1-0:2.7.0": obis_el("kW_min", 3, "All phases current production"),
    "1-0:21.7.0": obis_el("L1_plus", 3, "L1 consumption"),
    "1-0:41.7.0": obis_el("L2_plus", 3, "L2 consumption"),
    "1-0:61.7.0": obis_el("L3_plus", 3, "L3 consumption"),
    "1-0:22.7.0": obis_el("L1_min", 3, "L1 production"),
    "1-0:42.7.0": obis_el("L2_min", 3, "L2 production"),
    "1-0:62.7.0": obis_el("L3_min", 3, "L3 production"),
    "1-0:32.7.0": obis_el("V_L1", 3, "L1 voltage"),
    "1-0:52.7.0": obis_el("V_L2", 3, "L2 voltage"),
    "1-0:72.7.0": obis_el("V_L3", 3, "L3 voltage"),
    "1-0:31.7.0": obis_el("A_L1", 3, "L1 current"),
    "1-0:51.7.0": obis_el("A_L2", 3, "L2 current"),
    "1-0:71.7.0": obis_el("A_L3", 3, "L3 current"),
    "1-0:94.32.1": obis_el("V_grid", 1, "Grid Config: 230=3x230V, 400=3x400V"),
    "0-0:17.0.0": obis_el("kW_limit", 71, "Max power, 99.999 = deactivated"),
    "1-0:31.4.0": obis_el("A_limit", 21, "Max current, 999.99 = deactivated"),
    "1-0:1.6.0": obis_el("month_peak", 4, "Current Month Peak:Time/Power"),
    "0-0:98.1.0": obis_el("months_peak_past", 7, "Past Months (13) Peak:Time/Power"),
    "1-0:1.4.0": obis_el("quarter_peak", 5, "Quarter Hour Average Power"),
    "0-1:24.1.0": obis_el("dev_bus_1", 72, "Device Type Bus 1 (gas=3, water=7, ..)"),
    "0-2:24.1.0": obis_el("dev_bus_2", 72, "Device Type Bus 2 (gas=3, water=7, ..)"),
    "0-3:24.1.0": obis_el("dev_bus_3", 72, "Device Type Bus 3 (gas=3, water=7, ..)"),
    "0-4:24.1.0": obis_el("dev_bus_4", 72, "Device Type Bus 4 (gas=3, water=7, ..)"),
    "0-0:96.1.2": obis_el("ean_electr", 10, "EAN code Electricity"),
    "0-1:96.1.2": obis_el("ean_bus_1", 10, "EAN code Bus 1"),
    "0-2:96.1.2": obis_el("ean_bus_2", 10, "EAN code Bus 2"),
    "0-3:96.1.2": obis_el("ean_bus_3", 10, "EAN code Bus 3"),
    "0-4:96.1.2": obis_el("ean_bus_4", 10, "EAN code Bus 4"),
    "0-0:96.1.1": obis_el("meter_electr", 10, "Meter Serial Electricity"),
    "0-1:96.1.1": obis_el("meter_bus_1", 10, "Meter Serial Bus 1"),
    "0-2:96.1.1": obis_el("meter_bus_2", 10, "Meter Serial Bus 2"),
    "0-3:96.1.1": obis_el("meter_bus_3", 10, "Meter Serial Bus 3"),
    "0-4:96.1.1": obis_el("meter_bus_4", 10, "Meter Serial Bus 4"),
    "0-1:24.2.3": obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 1"),
    "0-2:24.2.3": obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 2"),
    "0-3:24.2.3": obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 3"),
    "0-4:24.2.3": obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 4"),
    "0-1:24.2.1": obis_el("water_meter", 4, "Water consumption / capture time, Bus 1"),
    "0-2:24.2.1": obis_el("water_meter", 4, "Water consumption / capture time, Bus 2"),
    "0-3:24.2.1": obis_el("water_meter", 4, "Water consumption / capture time, Bus 3"),
    "0-4:24.2.1": obis_el("water_meter", 4, "Water consumption / capture time, Bus 4"),
    "0-0:96.3.10": obis_el("breaker_0", 70, "Electricity: 0=OFF, 1=ON, 2=Ready Reconnect"),
    "0-1:96.3.10": obis_el("breaker_1", 70, "Virtual Relay Bus 1, 0=OFF, 1=ON"),
    "0-2:96.3.10": obis_el("breaker_2", 70, "Virtual Relay Bus 2, 0=OFF, 1=ON"),
    "0-3:96.3.10": obis_el("breaker_3", 70, "Virtual Relay Bus 3, 0=OFF, 1=ON"),
    "0-4:96.3.10": obis_el("breaker_4", 70, "Virtual Relay Bus 4, 0=OFF, 1=ON"),
    "0-1:24.4.0": obis_el("gas_breaker_1", 70, "Gas Valve Bus 1, 0=OFF, 1=ON, 2=Ready Reconnect"),
    "0-2:24.4.0": obis_el("gas_breaker_2", 70, "Gas Valve Bus 2, 0=OFF, 1=ON, 2=Ready Reconnect"),
    "0-3:24.4.0": obis_el("gas_breaker_3", 70, "Gas Valve Bus 3, 0=OFF, 1=ON, 2=Ready Reconnect"),
    "0-4:24.4.0": obis_el("gas_breaker_4", 70, "Gas Valve Bus 4, 0=OFF, 1=ON, 2=Ready Reconnect")
}

usage_columns = ["Day-3", "Day-2", "Day-1", "Today", "Week", "Month", "Year"]

# please note that "Σ € Utilities" is a calculated row (with strings) and is added to the table by the usage script
usage_rows = ["+Day", "-Day", "+Night", "-Night", "Σ kWh", "+€ Day", "-€ Day", "+€ Night", "-€ Night",
                            "Σ € kWh", "m3 Gas", "Σ € Gas", "m3 Water", "Σ € Water"]
rate_columns = ["Rate", "€/kWh Day", "€/kWh Night", "€/m3 Gas", "€/m3 Water"]
day_peak_columns = ["Day-3", "Day-2", "Day-1", "Today"]
