import pandas as pd
import mysql.connector
from mysql.connector import Error
from prepare_data import data_main

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            port=3307
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"Error: '{e}'")
    return connection

def create_database(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS countries_db")
        cursor.execute("USE countries_db")
        
        # Create table for countries data
        create_table_query = """
        CREATE TABLE IF NOT EXISTS countries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            capital VARCHAR(255),
            region VARCHAR(100),
            population BIGINT,
            flag VARCHAR(255),
            currency VARCHAR(10),
            rate DECIMAL(20,10),
            estimated_gdp DECIMAL(30,10),
            last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        print("Database and table created successfully")
    except Error as e:
        print(f"Error: '{e}'")

def populate_database(connection, df):
    cursor = connection.cursor()
    try:
        cursor.execute("USE countries_db")
        
        # First, clear existing data
        cursor.execute("TRUNCATE TABLE countries")
        
        # More thorough data cleaning
        df = df.assign(
            name=df['name'].fillna('Unknown'),
            capital=df['capital'].fillna(''),
            region=df['region'].fillna(''),
            population=df['population'].fillna(0),
            flag=df['flag'].fillna(''),
            currency=df['currency'].fillna(''),
            rate=df['rate'].fillna(0.0),
            estimated_gdp=df['estimated_gdp'].fillna(0.0)
        )
        
        # Convert specific columns to appropriate types
        df['population'] = df['population'].astype('Int64')
        df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
        df['estimated_gdp'] = pd.to_numeric(df['estimated_gdp'], errors='coerce')

        # Print debug information
        print("DataFrame columns:", df.columns.tolist())
        print("DataFrame dtypes:", df.dtypes)
        print("Sample row:", df.iloc[0].to_dict())
        
        # Prepare the insert query
        insert_query = """
        INSERT INTO countries (name, capital, region, population, flag, currency, rate, estimated_gdp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Convert DataFrame rows to list of tuples for bulk insert
        values = df[['name', 'capital', 'region', 'population', 'flag', 'currency', 'rate', 'estimated_gdp']].values.tolist()

        # Execute bulk insert
        cursor.executemany(insert_query, values)
        
        # Commit the transaction
        connection.commit()
        print(f"Successfully inserted {len(values)} records into the database")
    except Error as e:
        print(f"Error: '{e}'")
        # Print the problematic data if there's an error
        if 'values' in locals():
            print("First row being inserted:", values[0])
        connection.rollback()

def main():
    # Get the merged DataFrame from prepare_data.py
    merged_df = data_main()
    
    # Create database connection
    connection = create_connection()
    
    if connection is not None:
        # Create database and table
        create_database(connection)
        
        # Populate the database with data
        populate_database(connection, merged_df)
        
        # Close the connection
        connection.close()
    else:
        print("Failed to establish database connection")

if __name__ == "__main__":
    # Get the merged DataFrame from prepare_data.py
    main()


