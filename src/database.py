import sqlite3
import json
import os
from src.config import settings


class Database:
    def __init__(self, db_type=settings.DATABASE_TYPE, db_url=settings.DATABASE_URL):
        self.db_type = db_type
        self.db_url = db_url
        self.conn = None

    def connect(self):
        if self.db_type == "sqlite":
            os.makedirs(os.path.dirname(self.db_url), exist_ok=True)
            self.conn = sqlite3.connect(self.db_url)
            print(f"Connected to database: {self.db_url}")
        else:
            raise ValueError("Database Type not implemented")

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table(self, table_name: str, columns: dict):
        """Create a table with the specified columns"""
        self.connect()
        columns_def = ', '.join(f'{col} TEXT' for col in columns)
        try:
            print(f"Trying to create table {table_name} with {columns_def}")
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})")
        except Exception as e:
            print(f"Error creating the table {e}")
        finally:
            self.close()

    def insert_data(self, table_name: str, data: dict, pydantic_class):
        """Insert data into a specified table."""
        self.connect()
        try:
            print(f"Starting insert data into {table_name}")
            columns = ', '.join([k for k in pydantic_class.model_fields])
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
                        print(f"Updating data with query: {query} with values {values}")
                        self.conn.execute(query, values)
                        self.conn.commit()
                        print(f"Successfully updated data")
                    except Exception as e:
                        print(f"Error with updating query {e}")
                else:
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    try:
                        print(f"Inserting data with query: {query} with values {values}")
                        self.conn.execute(query, values)
                        self.conn.commit()
                        print(f"Successfully saved data")
                    except Exception as e:
                        print(f"Error with inserting query {e}")
            else:
                print("Error with contact info")
        
        except Exception as e:
            print(f"General error in insert_data: {e}")
        
        finally:
            self.close()

    def clear_table(self, table_name: str):
        """Clears all data from a specified table."""
        print(f"Starting clear table {table_name}")
        self.connect()
        try:
          print(f"Connected to db for clear table")
          print(f"Clearing all data from table {table_name}")
          self.conn.execute(f"DELETE FROM {table_name}")
          self.conn.commit()
          print(f"Successfully cleared data from {table_name}")
        except Exception as e:
           print(f"Error clearing the table {e}")

        finally:
          self.close()

    def fetch_data(self, table_name: str, query: str, params: tuple = ()):
        """Fetch data from the table based on a query"""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        self.close()
        return results

    def load_from_json(self, file_path, table_name, columns):
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
            print(f"Error inserting data: {e}")
        finally:
            self.close()
    