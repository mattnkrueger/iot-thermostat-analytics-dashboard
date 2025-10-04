from sqlalchemy import create_engine, func, Integer, String, Time, Float, UniqueConstraint
from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from typing import Optional
import os

# ================================================== SQL ALCHEMY ================================================== 
# this is a super easy to use python package for handling transactional database connections agnostically using OOP
# docs: https://www.sqlalchemy.org/
# we are using postgres, which requires a configuration... see the docker compose file and .env for the configs

# ================= BASE  ==================
# this classname doesnt need to be "Base", 
# however, passing DeclarativeBase (via orm)
# creates a Base class which we can extend
# to use SQLAlchemy's ORM functionality.
# Extending Base declares any child class
# as a Database Table with the following:
# __tablename__ : the name of the table
# attributes : fields of the table
#
# This is simply DDL; calling
#     Base.metadata.create_all(engine)
# executes the creation of the tables
#     Base.metadata.drop_all(engine)
# destroys all tables.
# 
# USAGE:
# - run this script directly; do not use
#   DDL at runtime. Instead, use the DML 
#   methods within db_methods.py
class Base(DeclarativeBase):
    pass

class Temperature(Base):
    """A sensor reading within 'temperature_readings'"""
    __tablename__ = "temperature_readings"

    id: Mapped[int]              = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str]       = mapped_column(String, nullable=False)
    timestamp: Mapped[str]       = mapped_column(String, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=True)

    def __repr__(self):
        return f"<temperature_readings(sensor_id={self.sensor_id}, timestamp={self.timestamp}, temperature_c={self.temperature_c})>"

class User(Base):
    """A user's configuration within 'user_configurations'"""
    __tablename__ = "user_configurations"

    user_id: Mapped[int]              = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name: Mapped[str]                 = mapped_column(String(30), nullable=False)
    email_addr: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    min_thresh_c: Mapped[int]         = mapped_column(Integer, default=32)            # approx 90 f
    max_thresh_c: Mapped[int]         = mapped_column(Integer, default=10)            # approx 50 f   

    __table_args__ = (
        UniqueConstraint("email_addr"),            
    )

    def __repr__(self):
        return f"<user_configurations(user_id={self.user_id}, name={self.name}, email_addr={self.email_addr}, min_thresh_c={self.min_thresh_c}, max_thresh_c={self.max_thresh_c}>"
