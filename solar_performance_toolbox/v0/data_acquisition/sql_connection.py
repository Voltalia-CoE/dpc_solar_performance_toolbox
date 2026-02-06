from os.path import join as ospathjoin
import pathlib
import urllib

from dotenv import dotenv_values
from sqlalchemy import create_engine


class SQLConnection:
    def __init__(self, country="PT") -> None:

        try:
            config = dotenv_values(ospathjoin(pathlib.Path(__file__).parent.resolve(), f"{country}.env"))
            conn = (
                "Driver={ODBC Driver 17 for SQL Server};"
                f'Server={config["Server"]},1433;'
                f'Database={config["Database"]};'
                f'Uid={config["Uid"]};'
                f'Pwd={config["Pwd"]};'
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
            )
            quoted = urllib.parse.quote_plus(conn)
            new_con = "mssql+pyodbc:///?odbc_connect={}".format(quoted)
            self.engine = create_engine(new_con, echo=False)
        except Exception as exc:
            config = dotenv_values(ospathjoin(pathlib.Path(__file__).parent, f"{country}.env").replace("\\..", ""))
            conn = (
                "Driver={ODBC Driver 17 for SQL Server};"
                f'Server={config["Server"]},1433;'
                f'Database={config["Database"]};'
                f'Uid={config["Uid"]};'
                f'Pwd={config["Pwd"]};'
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
            )
            quoted = urllib.parse.quote_plus(conn)
            new_con = "mssql+pyodbc:///?odbc_connect={}".format(quoted)
            self.engine = create_engine(new_con, echo=False)
