# from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey

import datetime
import os
from abc import ABC, abstractmethod

import sqlalchemy
from sqlalchemy import (Boolean, Column, ForeignKey, Integer, MetaData, String,
                        Table, create_engine, text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, sessionmaker


class software_item:
    def __init__(self, name, path, database, installed, env_path) -> None:
        self.name = name
        self.path = path
        self.database = database
        self.installed = installed
        self.env_path = env_path
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")

    def __repr__(self) -> str:
        return f"({self.name}, {self.path}, {self.database}, {self.installed}, {self.env_path})"


class database_item:
    def __init__(self, name, path, installed, software: str = "none") -> None:
        self.name = name
        self.path = path
        self.installed = installed
        self.software = software
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")

    def __repr__(self) -> str:
        return f"({self.name}, {self.path}, {self.installed})"


class Utility_Repository:

    database_item = database_item
    software_item = software_item
    dbtype_local: str = "sqlite"

    tables: list = ["software", "database"]

    def __init__(self, db_path="", install_type="local") -> None:
        self.db_path = db_path
        self.metadata = MetaData()

        self.setup_engine(install_type)

        self.create_tables()

    def clear_existing_repo(self):
        """
        Delete the database
        """

        self.metadata.drop_all(self.engine)

    def setup_engine(self, install_type):
        if install_type == "local":
            self.setup_engine_local()
        elif install_type == "docker":
            self.setup_engine_docker()

        self.clear_existing_repo()

    def setup_engine_local(self):
        self.engine = create_engine(
            f"{self.dbtype_local}:////"
            + os.path.join(*self.db_path.split("/"), "utility_local.db")
        )

    def setup_engine_postgres(self):

        from decouple import config

        self.engine = create_engine(
            f"postgresql+psycopg2://{config('DB_USER')}:{config('DB_PASSWORD')}@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}"
        )

    def setup_engine_docker(self):

        self.engine = create_engine(
            f"{self.dbtype_local}:////"
            + os.path.join(*self.db_path.split("/"), "utility_docker.db")
        )

    def create_software_table(self):

        self.software = Table(
            "software",
            self.metadata,
            Column("name", String),
            Column("path", String),
            Column("database", String),
            Column("installed", Boolean),
            Column("env_path", String),
            Column("date", String),
        )

        self.engine_execute(
            "CREATE TABLE IF NOT EXISTS software (name TEXT, path TEXT, database TEXT, installed BOOLEAN, env_path TEXT, date TEXT)"
        )

    def create_database_table(self):
        self.database = Table(
            "database",
            self.metadata,
            Column("name", String),
            Column("path", String),
            Column("installed", Boolean),
            Column("software", String),
            Column("date", String),
        )

        self.engine_execute(
            "CREATE TABLE IF NOT EXISTS database (name TEXT, path TEXT, installed BOOLEAN, software TEXT, date TEXT)"
        )

    def delete_tables(self):
        self.delete_table("software")
        self.delete_table("database")

    def delete_table(self, table_name):
        self.engine_execute(f"DROP TABLE {table_name}")

    def clear_tables(self):
        self.clear_table("software")
        self.clear_table("database")

    def clear_table(self, table_name):
        self.engine_execute(f"DELETE FROM {table_name}")

    def print_table_schema(self, table_name):
        print(self.engine_execute(
            f"PRAGMA table_info({table_name})").fetchall())

    def reset_tables(self):
        """
        Create the tables
        """
        self.clear_tables()

        self.metadata.create_all(self.engine)

    def engine_execute(self, string: str):
        sql = text(string)
        with self.engine.connect() as conn:

            result = conn.execute(sql)

            # conn.commit()

        return result

    def create_tables(self):
        """
        Create the tables
        """
        self.create_software_table()
        self.create_database_table()

        self.metadata.create_all(self.engine)

    def dump_software(self, directory: str):
        """
        Dump the software table to a tsv file
        """
        self.dump_table_tsv("software", directory)

    def dump_database(self, directory: str):
        """
        Dump the database table to a tsv file
        """

        self.dump_table_tsv("database", directory)

    def dump_table_tsv(self, table_name: str, directory: str):
        """
        Dump a table to a tsv file
        """

        if table_name not in self.tables:
            print(
                f"Table {table_name} not found. Available tables: {self.tables}")
            return

        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        table_rows = self.engine.execute(f"SELECT * FROM {table_name}")
        print("### TABLE ROWS ###")
        print(table_rows)

        with open(os.path.join(directory, f"{table_name}.tsv"), "w") as f:
            for row in table_rows:
                f.write("\t".join([str(x) for x in row]) + "\n")

    def get(self, table_name, id):
        """
        Get a record by id from a table
        """

        return self.engine_execute(f"SELECT * FROM {table_name} WHERE name='{id}'")

    def check_exists(self, table_name, id):
        """
        Check if a record exists in a table
        """

        find = self.engine_execute(
            f"SELECT * FROM {table_name} WHERE name='{id}'"
        ).fetchall()
        find = len(find) > 0
        if find:
            return True
        else:
            return False

    @abstractmethod
    def add_software(self, item: software_item):
        """
        Add a record to a table
        """
        # print("adding software")

        self.engine_execute(
            f"INSERT INTO software (name, path, database, installed, env_path, date) VALUES ('{item.name}', '{item.path}', '{item.database}', '{item.installed}', '{item.env_path}', '{item.date}')"
        )

    @abstractmethod
    def add_database(self, item: database_item):
        """
        Add a record to a table
        """

        self.engine_execute(
            f"INSERT INTO database (name, path, installed, date) VALUES ('{item.name}', '{item.path}', '{item.installed}', '{item.date}')"
        )
