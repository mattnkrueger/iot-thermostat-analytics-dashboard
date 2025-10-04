# from dash import html
# import dash_bootstrap_components as dcc
# import dash_mantine_components as dmc
# from db.db_methods import DB

#============================================================================
#                             ANALYTICS PAGE: DNF 
#============================================================================
#
# THIS FUNCTIONALITY WAS NOT PART OF THE REQUIREMENTS.
# additionally, given the small data schema (sensor, timestamp, temperature) 
# there really wasnt much analytics to perform
# 
# if the system was iterated upon, this is what i would add:
# - add humidity sensor for inside
# - add humidity sensor for outside
# - add temperature sensor for inside
# - add temperature sensor for outside
# - retrofit a IoT device to the AC/Heater (or buy a smart device)
#
# this could create a smart thermostat system:
# - cron scheduling for morning::warm and sleep::cold 
# - responsive indoor temperature changes to outside temp and humidity
# - analysis of the temperature and monthly electric bill

# class AnalyticsPage:
#     def __init__(self, app, db: DB):
#         self.DB = db

#         if app is not None:
#             self.callbacks()

#     def layout(self):
#         refresh_btn = dmc.Button(
#             id="refresh-btn",
#             children="Refresh",
#             size="md"
#         )

#         unit_dropdown = dmc.Select(
#             id="unit-dropdown-analytics",
#             data=[
#                 {"value": "C", "label": "Celcius (°C)"},
#                 {"value": "F", "label": "Fahrenheit (°F)"},
#             ],
#             value="c",
#             size="md",
#             persistence=True
#         )

#         return html.Div(
#             [
#                 dcc.Store(id="analytics")
#             ]
#         )

#     def callbacks(self):
#         @callback(
#             Output("daily-avg-graph", "data"),
#             Output("daily-min-text", "children"),
#             Output("daily-max-text", "children"),
#             Output("daily-stddev-text", "children"),
#             Output("daily-var-text", "children"),

#             Output("analytics", "data"),

#             Input("refresh-btn", "n_clicks"),
#             Input("unit-dropdown-analytics", "value"),
#             State("analytics", data)
#         )
#         def update_analytics(n_clicks, unit, cache):
#             if cache.get("daily_avg_df"):
#                 daily_avg_df = cache.get("daily_avg_df")
#             else:
#                 daily_avg_df = self.DB.get_daily_avgerages()
#                 cache["daily_avg_df"] = to_json(daily_avg_df)

#             if cache.get("daily_min_df"):
#                 daily_min_df = cache.get("daily_min_df")
#             else:
#                 daily_min_df = self.DB.get_daily_minimums()
#                 cache["daily_min_df"] = to_json(daily_min_df)

#             if cache.get("daily_max_df"):
#                 daily_max_df = cache.get("daily_max_df")
#             else:
#                 daily_max_df = self.DB.get_daily_maximums()
#                 cache["daily_max_df"] = to_json(daily_max_df)

#             if cache.get("daily_mode_df"):
#                 daily_mode_df = cache.get("daily_mode_df")
#             else:
#                 daily_mode_df = self.DB.get_daily_mode()
#                 cache["daily_mode_df"] = to_json(daily_mode_df)

#             return None, None, None, None, None, None
