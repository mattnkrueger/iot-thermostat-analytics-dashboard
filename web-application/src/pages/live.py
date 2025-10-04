from dash import Input, Output, callback, ctx, html, State, dcc, no_update
from numpy import nan_to_num
import dash_mantine_components as dmc
import pandas as pd
from io import StringIO
from utils.temperature_utils import c_to_f, c_to_k
from utils.process_stream import process_stream

from components.aio.thermostat_card import ThermostatCardAIO, RANGE_C, RANGE_F

pd.set_option("display.max_rows", 20)
pd.set_option("display.max_columns", 20)

SENSOR_1_COLOR = "#e85d04"
SENSOR_2_COLOR = "#ffba08"

def nan_to_none(temp):
    return None if pd.isna(temp) else temp

class LivePage:
    def __init__(self, app, redis, mode):
        self.red = redis
        self.MODE = mode
        
        if app is not None:
            self.callbacks()

    def layout(self):
        card_1 = ThermostatCardAIO("Sensor 1", aio_id="1", color=SENSOR_1_COLOR)
        card_2 = ThermostatCardAIO("Sensor 2", aio_id="2", color=SENSOR_2_COLOR)

        status_badge = dmc.Group(
            [
                dmc.Badge(id="system-status-badge", variant="dot", size="xl")
            ], 
            grow=True,
            align="center"
        )

        system_cards = dmc.Stack(
            [
                card_1,
                card_2
            ],
            justify="center",
            align="center"
        )

        line_chart = dmc.Card(
            dmc.LineChart(
                id="readings-chart",
                h=350,
                w=350,
                data=[],
                series=[
                    {"name": "Sensor 1", "color": SENSOR_1_COLOR},
                    {"name": "Sensor 2", "color": SENSOR_2_COLOR},
                ],
                dataKey="date",
                curveType="Monotone",

                tickLine="y",
                gridAxis="x",
                withXAxis="True",
                xAxisProps={"domain": [300, 0]}
   ,            xAxisLabel="Timestamp",

                withYAxis="True",
                yAxisLabel="Temperature",

                withDots="True",
                withLegend=True,
                connectNulls=False,
                dotProps={"r":2}
            ),
            withBorder=True,
        )

        segment = dmc.SegmentedControl(
            id="unit-select",
            data=[
                {"value": "C", "label": "Celcius (°C)"},
                {"value": "F", "label": "Fahrenheit (°F)"},
            ],
            value="C",
            size="md",
        )

        clear = dmc.Button(
            id="clear-stream",
            children="Clear",
            size="md"
        )

        clear = dmc.Button(
            id="clear-stream",
            children="Clear",
            size="md"
        )

        return dmc.Stack(
            [
                dcc.Interval(
                    id="system-clock",
                    interval=500,   
                    n_intervals=0
                ),
                status_badge,
                system_cards,
                dmc.Group(
                    [
                        segment,
                        clear,
                    ],
                ),

                line_chart,
                html.Div(id="empty")
            ],
            justify="flex-start",
            align="center"
        )

    def get_segment_color(self, status:str):
        if status == "ON":
            return "green"
        elif status == "OFF":
            return "red"
        else:
            return None

    def callbacks(self):
        @callback(
            Output("readings-chart", "data"),
            Output("readings-chart", "unit"),
            Output("readings-chart", "yAxisProps"),
            Output(ThermostatCardAIO.ids.data("1"), "data"),
            Output(ThermostatCardAIO.ids.data("2"), "data"),
            Input("system-clock", "n_intervals"),
            Input("unit-select", "value"),
            Input(ThermostatCardAIO.ids.segmented_control("1"), "value"),   # added for testing mode
            Input(ThermostatCardAIO.ids.segmented_control("2"), "value"),
        )
        def update_chart(n_intervals, unit, val1, val2):
            if ctx.triggered_id == "unit-select":       # virtualize (placing here as there is not a physical switch --> no logic needed)
                self.red.set("temperatureUnit", unit)

            data_1 = self.red.xrevrange(name="readings:1", count=300)
            data_2 = self.red.xrevrange(name="readings:2", count=300)

            df = (process_stream(data_1, data_2))

            if df is not None:
                df = df.where(pd.notna(df), None)
                try:
                    first_row = df.iloc[[-1]]
                    sensor_1_temp = nan_to_none(first_row.iloc[0]["Sensor 1"])
                    sensor_2_temp = nan_to_none(first_row.iloc[0]["Sensor 2"])
                except:
                    sensor_1_temp = None
                    sensor_2_temp = None

                temperature_cols = ["Sensor 1", "Sensor 2"]
                if unit == "F":
                    df[temperature_cols] = df[temperature_cols].apply(c_to_f)
                    range_y = [RANGE_F[0], RANGE_F[-1]]
                else:
                    range_y = [RANGE_C[0], RANGE_C[-1]]
                
                df["date"] = pd.to_datetime(df["date"], unit="s")
                df["date"] = df["date"].dt.tz_localize("UTC")
                df["date"] = df["date"].dt.tz_convert("America/Chicago")
                df["date"] = df["date"].dt.time
            else:
                first_row = "NO DATA"
                sensor_1_temp = None
                sensor_2_temp = None
                range_y = [RANGE_C[0], RANGE_C[-1]]

            records = df.to_dict("records")

            is_unplugged_1 = self.red.get("sensor:1:unplugged")
            is_unplugged_2 = self.red.get("sensor:2:unplugged")

            sensor_1_temp = "UNPLUGGED" if is_unplugged_1 == "true" else sensor_1_temp
            sensor_2_temp = "UNPLUGGED" if is_unplugged_2 == "true" else sensor_2_temp

            if self.MODE == "testing":
                if val1 == "OFF":
                    sensor_1_temp = None
                if val2 == "OFF":
                    sensor_2_temp = None
                    
            thermostat_card_1 = {"reading": str(sensor_1_temp)}
            thermostat_card_2 = {"reading": str(sensor_2_temp)}

            # range of chart
            yAxisProps = {"domain":range_y}

            return records, f"°{unit.upper()}", yAxisProps, thermostat_card_1, thermostat_card_2

        @callback(
            Output("empty", "children"),
            Input("clear-stream", "n_clicks")
        )
        def clear_stream(n_clicks):
            if ctx.triggered_id == "clear-stream":          
                self.red.delete("readings:1")
                self.red.delete("readings:2")
            return [""]

        # ==========================================
        #              VIRTUALIZATION 
        # ==========================================
        @callback(
            Output(ThermostatCardAIO.ids.segmented_control("1"), "disabled"),
            Output(ThermostatCardAIO.ids.segmented_control("1"), "value"),
            Output(ThermostatCardAIO.ids.segmented_control("1"), "color"),
            Input("system-clock", "n_intervals"),
            Input(ThermostatCardAIO.ids.segmented_control("1"), "value")
        )
        def toggle_sensor_1(n_intervals, wanted):
            actual = self.red.get("virtual:1:status")

            # testing (immediate update)
            if self.MODE == "testing" and wanted != actual:
                self.red.set("virtual:1:wants_toggle", "true")
                color = "green" if wanted == "ON" else "red"
                return False, wanted, color

            # real mode (change takes effect after 1 second)
            if ctx.triggered_id == ThermostatCardAIO.ids.segmented_control("1"):
                if wanted != actual:              
                    self.red.set("virtual:1:wants_toggle", "true")
                    return no_update, no_update, no_update

            # device status
            status = self.red.get("systemStatus")
            if status == "DISCONNECTED":
                return True, None, None

            if actual == "ON":
                return False, actual, "green"

            if actual == "OFF":
                return False, actual, "red"

            is_unplugged = self.red.get("sensor:1:unplugged")
            if is_unplugged == "true":
                return True, None, None

            return no_update, no_update, no_update

        @callback(
            Output(ThermostatCardAIO.ids.segmented_control("2"), "disabled"),
            Output(ThermostatCardAIO.ids.segmented_control("2"), "value"),
            Output(ThermostatCardAIO.ids.segmented_control("2"), "color"),
            Input("system-clock", "n_intervals"),
            Input(ThermostatCardAIO.ids.segmented_control("2"), "value")
        )
        def toggle_sensor_2(n_intervals, wanted):
            actual = self.red.get("virtual:2:status")

            # testing (immediate update)
            if self.MODE == "testing" and wanted != actual:
                self.red.set("virtual:2:wants_toggle", "true")
                color = "green" if wanted == "ON" else "red"
                return False, wanted, color

            # virtualize
            actual = self.red.get("virtual:2:status")
            if ctx.triggered_id == ThermostatCardAIO.ids.segmented_control("2"):
                if wanted != actual:              
                    self.red.set("virtual:2:wants_toggle", "true")
                    return no_update, no_update, no_update

            # device status
            status = self.red.get("systemStatus")
            if status == "DISCONNECTED":
                return True, None, None

            if actual == "ON":
                return False, actual, "green"

            if actual == "OFF":
                return False, actual, "red"

            is_unplugged = self.red.get("sensor:2:unplugged")
            if is_unplugged == "true":
                return True, None, None

        # ==========================================
        #            HANDLE PHYSICAL SWITCH
        # ==========================================
        @callback(
            Output("system-status-badge", "color"),
            Output("system-status-badge", "children"),
            Input("system-clock", "n_intervals"),
        )
        def update_status(n_intervals):
            curr = self.red.get("systemStatus")
            status = "DISCONNECTED" if curr is None else curr
            if status == "CONNECTED":
                color = "green"
            elif status == "DISCONNECTED":
                color = "red"
            else:
                color = "blue"
            return color, [status]

