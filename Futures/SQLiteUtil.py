import os
import sqlite3
from .Util import read_csv


class SQLite:
    def __init__(self, database):
        self.conn = None
        self.__database = database
        self.__get_connection()

    def __get_connection(self):
        self.conn = sqlite3.connect(self.__database)

    def create_table(self, sqlite_table_name, sqlite_columns):
        create_template = "create table if not exists {table} ({column})"
        columns = ",".join("{} text".format(col) for col in sqlite_columns)
        create_query = create_template.format(table=sqlite_table_name, column=columns)
        self.conn.execute(create_query)
        self.conn.commit()

    def write_sqlite(self, path_str, table_name):
        insert_template = "insert into {table} values ({column})"
        if os.path.isdir(path_str):
            data = []
            for filename in os.listdir(path_str):
                data.extend(read_csv(os.path.join(path_str, filename)))
        else:
            filename = path_str
            data = read_csv(filename, with_header=True)
        columns = ",".join("?" for _ in range(len(data[0])))
        insert_query = insert_template.format(table=table_name, column=columns)
        self.conn.executemany(insert_query, data)
        self.conn.commit()

    def drop_table(self, table_name):
        self.conn.execute("drop table if exists %s" % table_name)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def tables(self):
        cursor = self.conn.execute("select name from sqlite_master where type='table'")
        return [result[0] for result in cursor.fetchall()]

    def get_columns(self, table_name):
        cursor = self.conn.execute("select sql from sqlite_master where name='{}'".format(table_name))
        result = cursor.fetchone()
        if result is None:
            return result
        else:
            result = result[0]
            result = result.split(table_name)[1]
            result = result.replace("(", "").replace(")", "").strip()
            result_list = result.split(",")
            columns = [col.split(" ")[0] for col in result_list]
            return columns


class SQLiteUtil(SQLite):
    def scan(self, query):
        cursor = self.conn.execute(query)
        return cursor.fetchall()
