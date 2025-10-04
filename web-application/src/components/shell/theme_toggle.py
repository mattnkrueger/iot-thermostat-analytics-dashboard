import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import Input, Output,  clientside_callback

theme_toggle = dmc.Switch(
    offLabel=DashIconify(icon="streamline-ultimate:light-mode-bright-dark-bold", width=17, color=dmc.DEFAULT_THEME["colors"]["yellow"][8]),
    onLabel=DashIconify(icon="streamline-ultimate:light-mode-bright-dark", width=17, color=dmc.DEFAULT_THEME["colors"]["yellow"][6]),
    id="theme",
    persistence=True,
    color="grey",
    size="lg",
)

clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute('data-mantine-color-scheme', switchOn ? 'dark' : 'light');
       return window.dash_clientside.no_update
    }
    """,
    Output("theme", "id"),
    Input("theme", "checked"),
)
