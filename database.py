import sqlite3
import typing


class WorkspaceData:
    def __init__(self):
        self.connection = sqlite3.connect("database.db")
        self.connection.row_factory = sqlite3.Row  # Makes the data retrieved from the database accessible by their column name
        self.cursor = self.connection.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT, exchange TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT,"
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")

        self.connection.commit()  # Saves the changes

    def get(self, table: str) -> typing.List[sqlite3.Row]:


        #Get all the rows recorded for the table.


        self.cursor.execute(f"SELECT * FROM {table}")
        workspace_data = self.cursor.fetchall()

        return workspace_data


    def save(self, table: str, data: typing.List[typing.Tuple]):

        #Erase the previous table content and record new data to it.


        self.cursor.execute(f"DELETE FROM {table}")

        table_data = self.cursor.execute(f"SELECT * FROM {table}")

        column = [description[0] for description in table_data.description]  # Lists the columns of the table

        # Creates the SQL insert statement dynamically
        insert_statement = f"INSERT INTO {table} ({', '.join(column)}) VALUES ({', '.join(['?'] * len(column))})"

        self.cursor.executemany(insert_statement, data)
        self.connection.commit()

