from ctypes import alignment
from dash import html, Output, Input, callback, ctx, no_update
from dash_iconify import DashIconify
import dash_ag_grid as dag
import os
import dash_mantine_components as dmc

DEFAULT_NAME_PLACEHOLDER = "Your Name"
DEFAULT_EMAIL_PLACEHOLDER = "Your Email"
DEFAULT_MIN_THRESH = 10
DEFAULT_MAX_THRESH = 30

def new_user_form_defaults() -> tuple:
    return (
        DEFAULT_MIN_THRESH,
        DEFAULT_MAX_THRESH,
        DEFAULT_EMAIL_PLACEHOLDER,
        None,
        DEFAULT_NAME_PLACEHOLDER,
        None
    )

def new_user_form_no_updates() -> tuple:
    return (
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
    )

def new_user_alert_props(alert_type:str) -> tuple:
    if alert_type == "e1":
        return (False, "red", "Error: one or more inputs are empty")
    elif alert_type == "e2":
        return (False, "red", "Error: a non-uiowa edu email was inputted")
    elif alert_type == "e3":
        return (False, "red", "Error: email already exists")
    elif alert_type == "s":
        return (False, "green", "Success: user added! Refresh to view.")
    elif alert_type == "x":
        return (False, "red", "Something unexpected happened. Try Again.")
    else:
        return (True, None, None)

def new_user_form():
    # name
    form_name = dmc.TextInput(
        id="new-user-name",
        label="Name",
        placeholder="Your Name",
        required=True,
    )

    # email
    form_email = dmc.TextInput(
        id="new-user-email",
        label="Email",
        placeholder="user@uiowa.edu",
        description="Must be a University of Iowa email (@uiowa.edu)",
        required=True,
    )

    # threshold min
    form_min_threshold_c = dmc.NumberInput(
        id="new-user-min-thresh",
        label="Minimum Threshold (°C)",
        min=0,
        max=50,
        value=10,
        step=1,
    ) 

    # threshold max
    form_max_threshold_c = dmc.NumberInput(
        id="new-user-max-thresh",
        label="Maximum Threshold (°C)",
        min=0,
        max=50,
        value=30,
        step=1,
    ) 


    submit_button = dmc.Button(
        id="new-user-submit",
        children=["Submit User"],
        color="green"
    )

    cancel_button = dmc.Button(
        id="new-user-cancel",
        children=["Cancel"],
        color="red",
        variant="outline"
    )

    button_row = dmc.Group(
        [
            submit_button, 
            cancel_button
        ], 
        justify="flex-end",
        mt="md"
    )

    form = dmc.Stack(
        [
            form_name,
            form_email,
            form_min_threshold_c,
            form_max_threshold_c,
            button_row
        ]
    )

    modal = dmc.Modal(
        title="Create a New User",
        id="new-user-modal",
        children=[
            form        
        ]
    )

    return modal
