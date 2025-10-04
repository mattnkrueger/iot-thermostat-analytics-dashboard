from dash import Dash, html, dcc, Input, Output, ctx
import dash_mantine_components as dmc
import redis
import os
import json
import pandas as pd

from pathlib import Path

from pages.live import LivePage
from pages.settings import SettingsPage

from components.shell.header import header
from components.shell.footer import footer
from celery import Celery

from db.db_methods import DB

# =================================================== #
#                                                     #
#                                                     #
#                   SETUP APPLICATION                 #
#                                                     #
#                                                     #
# =================================================== #
# ENVIRONMENT VARIABLES
HOST      = os.getenv("HOST", "localhost")         
DASH_PORT = os.getenv("DASH_PORT", "8050")         
SOCK      = os.getenv("SOCK")
DB_URL    = os.getenv("DB_URL")
MODE      = os.getenv("MODE")

if not HOST:
    raise RuntimeError("HOST env var is not set")
if not DASH_PORT:
    raise RuntimeError("PORT env var is not set")
if not SOCK:
    raise RuntimeError("SOCK env var is not set")
if not DB_URL:
    raise RuntimeError("DB_PATH env var is not set")

# DATABASE
DB = DB(db_path=DB_URL)

# REDIS STREAM + CACHE
red = redis.Redis(
    unix_socket_path=SOCK,
    decode_responses=True
)

# setup the user threshold dataframe to check
user_df: pd.DataFrame = DB.get_all_users()
if user_df is not None:
    user_records = user_df.to_dict()

    min_thresh = user_df["min_thresh_c"].max()
    max_thresh = user_df["max_thresh_c"].min()

    red.set("users_df", json.dumps(user_records))
    red.set("maxMinThresh", str(min_thresh))
    red.set("minMaxThresh", str(max_thresh))

# CELERY TASK QUEUE
celery_client = Celery(
    main=__name__,
    broker=f"redis+socket://{SOCK}",
)

# ===================================================
#                 DASH APPLICATION
# ===================================================
app = Dash(
    name="ECE Senior Design Lab 1", 
    assets_folder=str(Path.cwd() / "src" / "assets"),
    suppress_callback_exceptions=True
)

app.title = "Lab 1: ECE Senior Design"

live_page_obj      = LivePage(app=app, redis=red, mode=MODE)
settings_page_obj  = SettingsPage(app=app, db=DB, redis=red, celery=celery_client)

app.layout = dmc.MantineProvider(
    theme={
        "primaryColor": "yellow",
        "defaultRadius": "sm",
        "black": "#454545",  
        "components": {
            "Button": {
                "defaultProps": {
                    "shadow": "xs"
                }
            },
            "Card": {
                "defaultProps": {
                    "shadow": "xs",
                    "radius": "sm"
                }
            },
        },
    },
    children=[
        dcc.Location(id='url'),
        dmc.AppShell(
            [
                dmc.AppShellHeader(
                    header()
                ),
                dmc.AppShellMain(
                    dmc.Box(
                        id="page-content",
                        py="sm",
                        px="sm",
                    ),
                ),
                footer()
            ],
            header={"height":60, "width":"100%"},
        )
    ],
)

# PAGE ROUTING
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/' or pathname == '/live':
        return live_page_obj.layout()
    elif pathname == '/settings':
        return settings_page_obj.layout()
    else:
        return html.Div("404 Page Not Found")

# =================================================== #
#                                                     #
#                                                     #
#                   START APPLICATION                 #
#                                                     #
#                                                     #
# =================================================== #
if __name__ == '__main__':
    app.run(
        debug=True,
        port=DASH_PORT,
        host=HOST            
    )
