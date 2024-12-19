import sqlite3
import json
import os
from src.config import settings
import logging
from typing import List, Dict, Any, Tuple, Optional


class Database:
    """
    A class for managing database operations.
    """
    def __init__(self, db_type: str = settings.DATABASE_TYPE, db_url: str = settings.DATABASE_URL):
        """
        Initializes the Database object.
        
        Args:
            db_type: The type of the database (e.g., "sqlite").
            db_url: The URL of the database.
        """
        self.db_type = db_type
        self.db_url = db_url
        self.conn = None
        if self.db_type == "sqlite":
             os.makedirs(os.path.dirname(self.db_url), exist_ok=True)


    def connect(self) -> None:
        """Connects to the database."""
        try:
            if self.db_type == "sqlite":
                self.conn = sqlite3.connect(self.db_url)
                logging.info(f"Connected to database: {self.db_url}")
            else:
                raise ValueError(f"Database Type {self.db_type} not implemented")
        except sqlite3.Error as e:
             logging.error(f"Error connecting to the database: {e}")
             raise
    def close(self) -> None:
        """Closes the database connection."""
        if self.conn:
            try:
                self.conn.close()
                logging.info(f"Closed connection to database: {self.db_url}")
            except sqlite3.Error as e:
                logging.error(f"Error closing database connection: {e}")


    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        Creates a table with specified columns.

        Args:
            table_name: The name of the table to create.
            columns: A dictionary where keys are column names and values are column types (e.g., {"name": "TEXT", "age": "INTEGER"}).
        """
        self.connect()
        try:
            columns_def = ', '.join(f'{col} {col_type}' for col, col_type in columns.items())
            logging.info(f"Trying to create table {table_name} with {columns_def}")
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})")
            # Explicitly add the interested_field_for_masters column
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            existing_columns = [col[1] for col in columns_info]
            if "interested_field_for_masters" not in existing_columns:
              logging.info(f"Adding missing column interested_field_for_masters to {table_name}")
              self.conn.execute(f"ALTER TABLE {table_name} ADD COLUMN interested_field_for_masters TEXT")


        except sqlite3.Error as e:
             logging.error(f"Error creating table {table_name}: {e}")
        finally:
             self.close()

    def insert_data(self, table_name: str, data: Dict[str, Any], pydantic_class) -> None:
        """
        Inserts data into the specified table.

        Args:
            table_name: The name of the table.
            data: A dictionary containing the data to insert, with keys as column names.
            pydantic_class: The Pydantic model class used for validation
        """
        self.connect()
        try:
            # Use pydantic_class.model_fields for column names
            columns = ', '.join(pydantic_class.model_fields)
            placeholders = ', '.join('?' for _ in pydantic_class.model_fields)

            # Convert lists to JSON string
            for key, value in data.items():
                if isinstance(value, list):
                    data[key] = json.dumps(value)
            values = tuple(data.values())
            contact_info = data.get('contact_info')

            if contact_info:
                query = f"SELECT COUNT(*) FROM {table_name} WHERE contact_info = ?"
                cursor = self.conn.cursor()
                cursor.execute(query, (contact_info,))
                count = cursor.fetchone()[0]

                if count > 0:
                    # Update the existing data
                    set_clause = ', '.join([f"{k} = ?" for k in pydantic_class.model_fields])
                    query = f"UPDATE {table_name} SET {set_clause} WHERE contact_info = ?"
                    values = tuple(list(data.values()) + [contact_info])
                    try:
                        logging.info(f"Updating data with query: {query} with values {values}")
                        self.conn.execute(query, values)
                        self.conn.commit()
                        logging.info("Successfully updated data")
                    except sqlite3.Error as e:
                       logging.error(f"Error updating data in {table_name}: {e}")

                else:
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    try:
                        logging.info(f"Inserting data with query: {query} with values {values}")
                        self.conn.execute(query, values)
                        self.conn.commit()
                        logging.info("Successfully inserted data")
                    except sqlite3.Error as e:
                         logging.error(f"Error inserting data into {table_name}: {e}")
            else:
                logging.error("Error with contact info")
        except sqlite3.Error as e:
            logging.error(f"Error during insert data into {table_name}: {e}")

        finally:
            self.close()


    def clear_table(self, table_name: str) -> None:
        """Clears all data from the specified table."""
        self.connect()
        try:
            logging.info(f"Clearing all data from table {table_name}")
            self.conn.execute(f"DELETE FROM {table_name}")
            self.conn.commit()
            logging.info(f"Successfully cleared data from {table_name}")
        except sqlite3.Error as e:
            logging.error(f"Error clearing table {table_name}: {e}")
        finally:
            self.close()


    def fetch_data(self, table_name: str, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Fetches data from the table based on a query.

        Args:
            table_name: The name of the table.
            query: The SQL query to execute.
            params: The parameters for the query.

        Returns:
            A list of dictionaries representing the results.
        """
        self.connect()
        try:
             cursor = self.conn.cursor()
             cursor.execute(query, params)
             results = cursor.fetchall()
             column_names = [description[0] for description in cursor.description]
             data = [dict(zip(column_names, row)) for row in results]
             return data
        except sqlite3.Error as e:
            logging.error(f"Error fetching data from {table_name}: {e}")
            return []
        finally:
             self.close()


    def load_from_json(self, file_path: str, table_name: str, columns: List[str]) -> None:
         """
         Loads data from a JSON file into the database table.

         Args:
            file_path: The path to the JSON file.
            table_name: The name of the database table.
            columns: A list of column names in the table
         """
         self.connect()
         try:
            with open(file_path, 'r') as f:
              data = json.load(f)
            for item in data:
              placeholders = ', '.join('?' for _ in columns)
              values = tuple(item.values())
              columns_str = ', '.join(columns)
              query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
              self.conn.execute(query, values)
            self.conn.commit()
         except Exception as e:
             logging.error(f"Error loading data from json into {table_name}: {e}")
         finally:
              self.close()