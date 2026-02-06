import pandas as pd
from sqlalchemy import __version__ as sqlv
from sqlalchemy.exc import OperationalError
from sqlalchemy import text, bindparam

from .BaseDataAcquisitor import BaseDataAcquisitor
from solar_performance_toolbox.v0.data_acquisition.sql_connection import SQLConnection

class DBDataAcquisitor(BaseDataAcquisitor):

    def __init__(self, sql_connection: SQLConnection | str = None, max_operational_retries: int = 3):
        super().__init__()
        
        self.sql_connection = sql_connection
        if sql_connection is None:
            self.sql_connection = SQLConnection()
        elif sql_connection.__class__ == str:
            self.sql_connection = SQLConnection(country=sql_connection)

        self.max_operational_retries = max_operational_retries

    def load_data(self, query, *args, **kwargs):

        # TODO: Update to use params properly

        current_try = 0
        while current_try < self.max_operational_retries:
            current_try += 1
            try:
                # use alternate reading query if pandas and sqlalchemy versions are not right
                # can be deleted once the correct versions are the default
                if (
                    float(".".join(pd.__version__.split(".")[0:2])) >= 2.2
                    and float(".".join(sqlv.split(".")[0:2])) < 2.0
                ):
                    with self.sql_connection.engine.connect() as conn:
                        data = pd.read_sql(sql=query, con=conn.connection, *args, **kwargs)
                    self.sql_connection.engine.dispose()
                    return data
                else:
                    data = pd.read_sql_query(query, self.sql_connection.engine, *args, **kwargs)
                    self.sql_connection.engine.dispose()
                    return data

            except OperationalError as exc:
                if current_try < self.max_operational_retries:
                    continue
                raise Exception(
                    "Something went wrong with the query - Operational Error: " + query
                ) from exc

            except Exception as exc:
                raise Exception(
                    "Something went wrong with the query: " + query
                ) from exc