from ctypes import alignment
from dash import html, Output, Input, callback, ctx, no_update
from dash_iconify import DashIconify
import dash_ag_grid as dag
import os
import dash_mantine_components as dmc
import pandas as pd

# forms are a perfect use case for dash all in one components
# whoops

def update_user_form_defaults() -> tuple:
    return (
        None, 
        None,
        None,
        None,
        None,
    )

def get_user_fields(row: pd.DataFrame) -> tuple:
    name       = row.iloc[0]["name"]
    email_addr = row.iloc[0]["email_addr"]
    min_thresh = row.iloc[0]["min_thresh_c"]
    max_thresh = row.iloc[0]["max_thresh_c"]

    return (name, email_addr, min_thresh, max_thresh)

def get_no_update_fields() -> tuple:
    name       = no_update
    email_addr = no_update    
    min_thresh = no_update
    max_thresh = no_update

    return (name, email_addr, min_thresh, max_thresh)

def update_user_alert_props(alert_type:str) -> tuple:
    if alert_type == "e1":
        return (False, "red", "Error: one or more inputs are empty")
    elif alert_type == "e2":
        return (False, "red", "Error: a non-uiowa edu email was inputted")
    elif alert_type == "e3":
        return (False, "red", "Error: email already exists")
    elif alert_type == "s":
        return (False, "green", "Success: user updated! Refresh to view.")
    elif alert_type == "x":
        return (False, "red", "Something unexpected happened. Try Again.")
    elif alert_type == "y":
        return (False, "red", "Please complete the form and try again.")
    else:
        return (True, None, None)

def update_user_form():
    # email (this drives the other fields)
    select_email = dmc.Select(
        id="uu-select",
        label="User Email",
        searchable=True,
        data=[],
        value="", 
        clearable=False,
        allowDeselect=False,
    )

    # name
    form_name = dmc.TextInput(
        id="uu-name",
        label="Name",
    )

    # threshold min
    form_min_threshold_c = dmc.NumberInput(
        id="uu-min-thresh",
        label="Minimum Threshold (°C)",
        min=0,
        max=50,
        step=1,
    ) 

    # threshold max
    form_max_threshold_c = dmc.NumberInput(
        id="uu-max-thresh",
        label="Maximum Threshold (°C)",
        min=0,
        max=50,
        step=1,
    ) 

    # 
    # FORM SUBMISSION (BASE)
    #
    submit_button = dmc.Button(
        id="uu-submit",
        children=["Submit Changes"],
        color="green"
    )

    cancel_button = dmc.Button(
        id="uu-cancel",
        children=["Cancel"],
        color="red",
        variant="outline"
    )

    delete_button = dmc.ActionIcon(
                    DashIconify(
                        icon="mdi:trash"
                    ),
                    id="uu-delete",
                    size="lg",
                    color="red"
                )

    button_row = dmc.Group(
        [
            delete_button,
            dmc.Group(
                [
                    submit_button, 
                    cancel_button,
                ],
            ),
        ], 
        justify="flex-end",
        mt="md"
    )

    #
    # DELETE FORM
    #
    confirm_delete_button = dmc.Button(
        id="uu-delete-confirm",
        children=["Delete User"],
        color="red",
        variant="outline"
    )

    confirm_delete_cancel_button = dmc.Button(
        id="uu-delete-cancel-confirm",
        children=["Cancel"],
        color="red",
        variant="outline"
    )

    #
    # SUBMIT
    #

    confirm_submit_button = dmc.Button(
        id="uu-submit-confirm",
        children=["Submit Changes"],
        color="green"
    )

    confirm_cancel_button = dmc.Button(
        id="uu-cancel-confirm",
        children=["Cancel"],
        color="red",
        variant="outline"
    )

    confirm_button_row = dmc.Group(
        [
            dmc.Group(
                [
                    confirm_submit_button,
                    confirm_cancel_button
                ]
            )
        ], 
        justify="flex-end",
        mt="md"
    )

    delete_confirm_button_row = dmc.Group(
        [
            dmc.Group(
                [
                    confirm_delete_button,
                    confirm_delete_cancel_button
                ]
            )
        ], 
        justify="flex-end",
        mt="md"
    )

    modal = dmc.Center([
        dmc.ModalStack(
            id="modal-stack",
            children=[
                dmc.ManagedModal(
                    id="uu-form",
                    title="Update an Existing User",
                    children=[
                        select_email,
                        form_name,
                        form_min_threshold_c,
                        form_max_threshold_c,
                        button_row
                    ],
                ),
                dmc.ManagedModal(
                    id="uu-update-form-confirm",
                    title="Confirm Update",
                    children=[
                        dmc.Text("Are you sure you want to perform this update?"),
                        confirm_button_row
                    ],
                ),
                dmc.ManagedModal(
                    id="uu-delete-form-confirm",
                    title="Confirm Deletion",
                    children=[
                        dmc.Text("Are you sure you want to delete this user?"),
                        delete_confirm_button_row
                    ],
                ),
            ]
        ),
    ])

    return modal


def delete_user_alert_props(alert_type):
    if alert_type == "e1":
        return (False, "red", "Error: one or more inputs are empty")
    elif alert_type == "e2":
        return (False, "red", "Error: a non-uiowa edu email was inputted")
    elif alert_type == "e3":
        return (False, "red", "Error: email already exists")
    elif alert_type == "s":
        return (False, "green", "Success: user removed! Refresh to view.")
    elif alert_type == "y":
        return (False, "red", "Please complete the form and try again.")
    else:
        return (True, None, None)
