from collections import UserString
from dash import html, Output, Input, callback, ctx, State, no_update
import redis
import dash_ag_grid as dag
import os
import dash_mantine_components as dmc
from celery import Celery
from dash_iconify import DashIconify
import pandas as pd
import json

from db.db_methods import DB
from components.new_user_form import new_user_form, new_user_form_defaults, new_user_form_no_updates, new_user_alert_props
from components.update_user_form import delete_user_alert_props, get_no_update_fields, update_user_form, get_user_fields, update_user_alert_props, update_user_form_defaults, delete_user_alert_props

class SettingsPage:
    def __init__(self, app, db: DB, redis, celery):
        self.DB = db
        self.red = redis
        self.celery_client=celery

        if app is not None:
            self.callbacks()

    def layout(self) -> html.Div:
        # buttons
        new_user_modal_btn = dmc.Button(
                id="new-user-modal-btn",
                children=["Add User"],
                leftSection=DashIconify(icon="qlementine-icons:new-16"),
                color="green"
        )

        update_user_modal_btn = dmc.Button(
                id="uu-open",
                children=["Edit User"],
                leftSection=DashIconify(icon="cuida:edit-outline"),
        )

        btn_group = dmc.Group(
            [
                new_user_modal_btn,
                update_user_modal_btn
            ],
            justify="flex-end",
            align="center"
        )

        # alerts
        new_user_modal_alert = dmc.Alert(
                id="new-user-alert",
                title="New User",
                duration=5000,
                withCloseButton=True,
                hide=True,
            )

        update_user_modal_alert = dmc.Alert(
                id="uu-alert",
                title="Update User",
                duration=5000,
                withCloseButton=True,
                hide=True,
            )

        delete_user_modal_alert = dmc.Alert(
                id="uu-delete-alert",
                title="Delete User",
                duration=5000,
                withCloseButton=True,
                hide=True,
            )

        # user table
        users_df = self.DB.get_all_users()
        user_table = dag.AgGrid(
            rowData=users_df.to_dict(orient="records"),
            columnDefs=[{"field": i} for i in users_df.columns],
            id="dag-users"
        )

        return dmc.Stack(
            [
                new_user_modal_alert,
                update_user_modal_alert,
                delete_user_modal_alert,
                html.Div(id="load"),
                dmc.Group(
                    [
                        dmc.Title("Settings"),
                        btn_group,
                    ],
                    justify="space-between",
                    align="center"
                ),
                user_table,
                new_user_form(),   # hidden modal
                update_user_form() # hidden modal
            ]
        )

    def handle_submit(self, email_addr, username, min_thresh, max_thresh, celery_task:str):
        try:
            # 1. check for fields
            fields = [min_thresh, max_thresh, email_addr, username]
            fields = [None if f in (None, "") else f for f in fields]

            error = "y"
            success = False
            if any(f is None for f in fields):
                error = "e1"
                success = False

            # 2. check for uiowa email
            elif not email_addr.endswith("@uiowa.edu"):
                error = "e2"
                success = False

            # 3. basic checks passed; check for existence
            elif celery_task == "add_user":
                exists = self.DB.does_email_exist(email_addr)
                if not exists:
                    error = ""
                    success = True
                else:
                    error = "e3"
                    success = False

            elif celery_task in ("update_user", "delete_user"):
                exists = self.DB.does_email_exist(email_addr)
                if exists:
                    error = ""
                    success = True
                else:
                    error = "e3"
                    success = False

            # 4. perform action
            if success:
                self.celery_client.send_task(
                    celery_task, 
                    kwargs={
                        "name":username,
                        "email_addr":email_addr,
                        "min_thresh_c":min_thresh,
                        "max_thresh_c":max_thresh,
                    }
                )

            return [error, success]
        except Exception as e:
            print("EXCEPTION - handle_submit()", e)
            return ["x", False]

    def update_cache_db(self, email_addr, username, min_thresh, max_thresh, celery_task:str):
        try:
            # ADD
            new = pd.DataFrame()
            old = json.loads(self.red.get("users_df"))
            users_df = pd.DataFrame.from_dict(old)

            if celery_task == "add_user":
                id = users_df["user_id"].max() + 1
                user = {
                    "user_id": id,
                    "name":username,
                    "email_addr": email_addr,
                    "min_thresh_c": min_thresh,
                    "max_thresh_c": max_thresh,
                }
                new = pd.concat([users_df, pd.DataFrame([user])], ignore_index=True)

            # UPDATE
            if celery_task == "update_user":
                users = users_df["email_addr"] == email_addr
                row = users_df.loc[users]

                user = row.index[0]

                users_df.at[user, "name"] = username
                users_df.at[user, "min_thresh_c"] = int(min_thresh)
                users_df.at[user, "max_thresh_c"] = int(max_thresh)


                new = users_df

            # DELETE
            if celery_task == "delete_user":
                mask = users_df["email_addr"] == email_addr
                row = users_df.loc[mask]

                new = users_df.drop(row.index).reset_index(drop=True)

            if not new.empty:
                new = new.drop_duplicates("email_addr", keep="first")

                new_min_thresh = new["min_thresh_c"].max()
                new_max_thresh = new["max_thresh_c"].min()

                self.red.set("users_df", new.to_json(orient="records"))
                self.red.set("maxMinThresh", str(new_min_thresh))
                self.red.set("minMaxThresh", str(new_max_thresh))
        except Exception as e:
            print("EXCEPTION - update_cache_db()", e)

    def callbacks(self):

        # ====================================
        #             THEME TOGGLE
        # ====================================
        @callback(
            Output("dag-users", "className"),
            Input("theme", "checked"),
        )
        def update_theme(switch_on):
            color = "ag-theme-alpine-dark" if switch_on else "ag-theme-alpine"
            return color

        # ====================================
        #             NEW USER FORM
        # ====================================
        @callback(
            Output("new-user-modal", "opened"),

            Output("new-user-alert", "hide"),
            Output("new-user-alert", "color"),
            Output("new-user-alert", "children"),

            Output("new-user-min-thresh", "value"),
            Output("new-user-max-thresh", "value"),
            Output("new-user-email", "placeholder"),
            Output("new-user-email", "value"),
            Output("new-user-name", "placeholder"),
            Output("new-user-name", "value"),

            Input("new-user-submit", "n_clicks"),
            Input("new-user-cancel", "n_clicks"),
            Input("new-user-modal-btn", "n_clicks"),

            State("new-user-modal", "opened"),
            State("new-user-min-thresh", "value"),
            State("new-user-max-thresh", "value"),
            State("new-user-email", "value"),
            State("new-user-name", "value"),
            prevent_initial_call=True,
        )
        def new_user_modal( submit, cancel, open, opened, min_thresh, max_thresh, email_addr, username): 
            trigger = ctx.triggered_id

            # open the modal
            if trigger == "new-user-modal-btn":
                return True, *(True, None,None), *new_user_form_defaults()

            # if user clicks submit button
            if trigger == "new-user-submit":

                error, success = self.handle_submit(email_addr=email_addr, username=username, min_thresh=min_thresh, max_thresh=max_thresh, celery_task="add_user")

                if success:
                    self.update_cache_db(email_addr=email_addr, username=username, min_thresh=min_thresh, max_thresh=max_thresh, celery_task="add_user")

                    return False, *new_user_alert_props("s"), *new_user_form_defaults()
                else:
                    return False, *new_user_alert_props(error), *new_user_form_no_updates()

            # cancel transaction
            if trigger == "new-user-cancel":
                return False, *(True, None, None), *new_user_form_defaults()

            else:
                return False, *(True, None, None), *new_user_form_no_updates()

        # ====================================
        #           UPDATE USER FORM 
        # ====================================
        @callback(
            Output("modal-stack", "open"),
            Output("modal-stack", "closeAll"),

            Output("uu-alert", "hide"),
            Output("uu-alert", "color"),
            Output("uu-alert", "children"),

            Output("uu-delete-alert", "hide"),
            Output("uu-delete-alert", "color"),
            Output("uu-delete-alert", "children"),

            Input("uu-delete", "n_clicks"),
            Input("uu-submit", "n_clicks"),
            Input("uu-submit-confirm", "n_clicks"),
            Input("uu-cancel", "n_clicks"),
            Input("uu-cancel-confirm", "n_clicks"),
            Input("uu-delete-confirm", "n_clicks"),
            Input("uu-delete-cancel-confirm", "n_clicks"),
            Input("uu-open", "n_clicks"),

            State("uu-select", "value"),
            State("uu-name", "value"),
            State("uu-min-thresh", "value"),
            State("uu-max-thresh", "value"),
            prevent_initial_call=True,
        )
        def update_user_modal(a,b,c,d,e,f,g,h,email_addr, username, min_thresh, max_thresh):
            trigger = ctx.triggered_id
            if trigger == "uu-open":
                return "uu-form", False, *update_user_alert_props(""), *delete_user_alert_props("")

            if trigger == "uu-submit":
                return "uu-update-form-confirm", False, *update_user_alert_props(""), *delete_user_alert_props("")

            if trigger == "uu-delete":
                return "uu-delete-form-confirm", False, *update_user_alert_props(""), *delete_user_alert_props("")

            if trigger == "uu-submit-confirm":
                error, success = self.handle_submit(email_addr=email_addr, username=username, min_thresh=min_thresh, max_thresh=max_thresh, celery_task="update_user")
                if success:
                    self.update_cache_db(email_addr=email_addr, username=username, min_thresh=min_thresh, max_thresh=max_thresh, celery_task="update_user")
                    return None, True, *update_user_alert_props("s"), *delete_user_alert_props("")
                else:
                    return None, True, *update_user_alert_props(error), *delete_user_alert_props("")

            if trigger == "uu-delete-confirm":
                error, success = self.handle_submit(email_addr=email_addr, username=username, min_thresh=min_thresh, max_thresh=max_thresh, celery_task="delete_user")
                if success:
                    self.update_cache_db(email_addr=email_addr, username=username, min_thresh=min_thresh, max_thresh=max_thresh, celery_task="delete_user")
                    return None, True, *update_user_alert_props(""), *delete_user_alert_props("s")
                else:
                    return None, True, *update_user_alert_props(""), *delete_user_alert_props(error), 

            if trigger in ("uu-cancel", "uu-cancel-confirm", "uu-delete-cancel-confirm"):
                return None, True, *update_user_alert_props(""), *delete_user_alert_props("")

        @callback(
            Output("uu-select", "value"),
            Output("uu-select", "data"),
            Input("uu-open", "n_clicks")
        )
        def update_email_selections(_):
            try:
                users = json.loads(self.red.get("users_df"))
                users_df = pd.DataFrame.from_dict(users)

                emails = users_df["email_addr"].tolist()
                data = [{"value": e, "label": e} for e in emails]
                val = data[0]
                return val, data
            except Exception as e:
                print("EXCEPTION - update_email_selections()", e)
                return None, None
                

        @callback(
            Output("uu-name", "value"),
            Output("uu-min-thresh", "value"),
            Output("uu-max-thresh", "value"),
            Input("uu-select", "value"),
            prevent_initial_call=True,
        )
        def populate_row(selected):
            try:
                users = json.loads(self.red.get("users_df"))
                users_df = pd.DataFrame.from_dict(users)
                row = users_df[users_df["email_addr"] == selected]

                if row.empty:
                    return no_update, no_update, no_update

                user = row.iloc[0]

                name = user["name"]
                min_thresh = int(user["min_thresh_c"])
                max_thresh = int(user["max_thresh_c"])

                return name, min_thresh, max_thresh
            except Exception as e:
                print("EXCEPTION - populate_row()", e)
                return None, None, None
