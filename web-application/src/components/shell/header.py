import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import Output, Input, callback, html, get_asset_url
from components.shell.theme_toggle import theme_toggle

LOGO_DARK = "iowa-gold.png"
LOGO_LIGHT = "iowa-black.png"

PAGE_LINKS= {
    # "System Architecture": "cbi:motion-sensor-temperature",
    "Live": "raphael:temp",    
    # "Analytics": "material-symbols:analytics-outline-rounded",        # DNF (see src/pages/analytics.py for future iteration)
    "Settings": "tabler:settings",
}

# ----- build menu items ---- #
# 1. Page links
page_items = []

for key,val in PAGE_LINKS.items():
    lower = key.lower()
    href = lower.replace(" ", "_")
    page_items.append(
        dmc.NavLink(
            label=dmc.Text(
                key, 
                fz={"base":18, "sm":14, "md":16, "lg":22}
            ),
            href=href,
            leftSection=DashIconify(icon=val, width=20),
        )
    )


# --------------------- HEADER --------------------- #

def header():
    lhs = dmc.Group(
        [
            dmc.Image(
                id="header-logo",
                w="90",
                h="45",
                fit="fit"
            ),
            html.Div(
                id="header-divider",
                style={
                        "background-color": "#c7c6c5",
                        "border-radius": "20px",
                        "width": "1px",
                        "height": "50%"
                }
            ),
            dmc.Title(
                "Herky's Nest",
                id="header-title",
                size="xl"
            )
        ],
        h="100%",
        px="md"
    )

    menu = dmc.Menu(
        [
            dmc.MenuTarget(
                dmc.ActionIcon(
                    DashIconify(
                        icon="stash:burger-classic-light"
                    ),
                    size="lg",
                    color=dmc.DEFAULT_THEME["colors"]["yellow"][6]
                ),
            ),
            dmc.MenuDropdown(
                [
                    dmc.MenuLabel(
                        "Pages",
                        fz="lg"
                    ),
                    *page_items,
                ]
            )
        ]
    )

    rhs = dmc.Center(
        [
            html.Div(
                theme_toggle, 
                style={
                    "marginRight":"1em"
                }
                ),
            menu
        ],
        h="100%",
    )

    return dmc.Group(
            [
                lhs,
                rhs
            ],
            h="100%",
            align="center",
            justify="space-between",
            px="sm"
        )

@callback(
    Output("header-logo", "src"),
    Output("header-title", "c"),
    Input("theme", "checked")
)
def header_theme_toggle(checked):
    if checked:  
        return get_asset_url(LOGO_DARK), "white"
    else:
        return get_asset_url(LOGO_LIGHT), dmc.DEFAULT_THEME["colors"]["yellow"][6]
