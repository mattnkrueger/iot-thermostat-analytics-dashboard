from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from sqlalchemy import engine, create_engine, delete
from sqlalchemy.orm import Session, sessionmaker
from pathlib import Path
import os
import redis
import smtplib
import json
import pandas as pd

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .db_orm import Temperature, User, Base

# ===================================================
#                EMAIL CONFIGURATION
# ===================================================
# this code was modified from Tejashree Salvi's Medium
# article: "Automating Emails with Python: A Comprehensive Guide"
# 
# her article was pretty comprehensive... not sure how 
# much more innovating can be done on top of smtplib so 
# cut and pasting and modifying for our needs.
SMTP_SERVER = 'ns-mx.uiowa.edu'
SMTP_PORT = 25
SMTP_USERNAME = 'lab1_seniordesign_team3@gmail.com'
SMTP_SENDER = SMTP_USERNAME

SOCK   = os.getenv("SOCK")
DB_URL = os.getenv("DB_URL")
MODE   = os.getenv("MODE")
# ===================================================
#                POSTGRES CONNECTION
# ===================================================
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)

# ===================================================
#                CELERY TASK QUEUE
# ===================================================
# building one engine (db conn) per worker. this is running with a pi4 
# so this entire setup is definitely overkill... it is possible that 
# we stick with the http sending of data from our temperature sensor 
# and use a more capable machine to reap the benefits of celery, task queues,
# database storage, and quicker analytics.
#
# the purpose of the initializer setup (and more importantly using sessionmaker)
# is to reduce the tcp handshaking required for making an engine connection. 
# The sessionmaker is a factory bound to the engine connection. This allows each task
# to simply borrow connections from the pool, perfom the insertion, and return the 
# connection to the pool
celery_app = Celery(
    main=__name__,
    broker=f"redis+socket://{SOCK}",
)

_engine = None
_Session = None

# ===================================================
#             CELERY WORKER MANAGEMENT
# ===================================================
@worker_process_init.connect
def initialize_new_worker(**kwargs):    
    global _engine, _Session                                    
    _engine = create_engine(DB_URL, echo=False)                     # NOTICE
    _Session = sessionmaker(bind=_engine, expire_on_commit=False)

@worker_process_shutdown.connect
def safely_destroy_worker(**_):
    _engine.dispose()

# ===================================================
#             CELERY ASYNC TASKS ENDPOINTS
# ===================================================
@celery_app.task(name="insert_record")
def insert_record(sensor_id, timestamp, temperature_c):
    session = _Session()
    try:
        reading = Temperature(sensor_id=sensor_id, timestamp=timestamp, temperature_c=temperature_c)
        session.add(reading)
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

@celery_app.task(name="add_user")
def add_user(name, email_addr, min_thresh_c, max_thresh_c):
    session = _Session()
    try:
        user = User(name=name, email_addr=email_addr, min_thresh_c=min_thresh_c, max_thresh_c=max_thresh_c)
        session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

@celery_app.task(name="delete_user")
def delete_user(name, email_addr, min_thresh_c, max_thresh_c):
    session = _Session()
    try:
        stmt = (
            delete(User)
            .where(User.email_addr == email_addr)
        )
        session.execute(stmt)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@celery_app.task(name="update_user")
def update_user(name, email_addr, min_thresh_c, max_thresh_c):
    try:
        print("UPDATING USER ", name)
        print("UPDATING USER ", email_addr)
        with Session(_engine) as session:
            updated = session.query(User).filter(User.email_addr == email_addr).update(
                {
                    "name": name,
                    "min_thresh_c": min_thresh_c,
                    "max_thresh_c": max_thresh_c,
                }
            )
            session.commit()
    except Exception as e:
        print("ERROR UPDATING", e)

@celery_app.task(name="email_min_thresh", autoretry_for=(smtplib.SMTPException,), retry_backoff=True, max_retries=5)
def email_min_thresh(sensor_id, df, last_three_list):
    if MODE == "testing":
        return 
    stmt = f"Cold Advisory: Sensor {sensor_id} read three consecutive readings over"

    mailing_list = get_mailing_list_min_thresh(df, last_three_list)
    print("SENDING MIN THRESH")
    for _, row in mailing_list.iterrows():
        name = row["name"]
        email_addr = row["email_addr"]
        min_thresh = row["min_thresh_c"]
        
        print("name", name)
        print("email", email_addr)
        print("min_thresh", min_thresh)

        message = (
            f"Attention {name}:\n"
            f"{stmt} {float(min_thresh):.2f} °C\n\n"
            f"Readings: {last_three_list}"
        )
        msg = MIMEText(message)
        msg["Subject"] = "ECE Senior Design Lab 1 - Critical Temperature Reading!"
        msg["From"] = SMTP_USERNAME
        msg["To"] = email_addr
        print("SENT!")

        with smtplib.SMTP("ns-mx.uiowa.edu", 25) as server:
            server.sendmail(SMTP_USERNAME, [email_addr], msg.as_string())

@celery_app.task(name="email_max_thresh", autoretry_for=(smtplib.SMTPException,), retry_backoff=True, max_retries=5)
def email_max_thresh(sensor_id, df, last_three_list):
    if MODE == "testing":
        return 
    stmt = f"Heat Advisory: Sensor {sensor_id} read three consecutive readings over"

    mailing_list = get_mailing_list_max_thresh(df, last_three_list)
    print("SENDING MAX THRESH")
    for _, row in mailing_list.iterrows():
        name = row["name"]
        email_addr = row["email_addr"]
        min_thresh = row["min_thresh_c"]

        print("name", name)
        print("email", email_addr)
        print("min_thresh", min_thresh)

        message = (
            f"Attention {name}:\n"
            f"{stmt} {float(min_thresh):.2f} °C\n\n"
            f"Readings: {last_three_list}"
        )
        msg = MIMEText(message)
        msg["Subject"] = "ECE Senior Design Lab 1 - Critical Temperature Reading!"
        msg["From"] = SMTP_USERNAME
        msg["To"] = email_addr

        print("SENT!")

        with smtplib.SMTP("ns-mx.uiowa.edu", 25) as server:
            server.sendmail(SMTP_USERNAME, [email_addr], msg.as_string())

def get_mailing_list_min_thresh(df, temps):
    temps = [float(temp) for temp in temps]

    df = json.loads(df)
    users_df = pd.DataFrame.from_dict(df)

    max_min = max(temps)
    wanted = users_df["min_thresh_c"].astype(float) > max_min

    return users_df.loc[wanted]

def get_mailing_list_max_thresh(df, temps):
    temps = [float(temp) for temp in temps]

    df = json.loads(df)
    users_df = pd.DataFrame.from_dict(df)

    min_max = max(temps)
    wanted = users_df["max_thresh_c"].astype(float) < min_max

    return users_df.loc[wanted]
