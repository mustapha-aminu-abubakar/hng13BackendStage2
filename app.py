from flask import Flask, jsonify, request
import pandas as pd
from create_db import main, create_connection
from datetime import datetime, timezone
app = Flask(__name__)

last_refresh = None

@app.route('/countries/refresh', methods=['POST'])
def populate_db_route():
    try:
        last_refresh = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        main()  # Call the main function from create_db.py to populate the database
        return jsonify({"message": f"Database populated successfully at {last_refresh}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/countries', methods=['GET'])
def get_countries():
    try:
        # Get query parameters
        filters = request.args.to_dict()
        
        # Fetch countries data from the database
        connection = create_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute("USE countries_db")
            
            # Start with base query
            query = "SELECT * FROM countries WHERE 1=1"
            params = []
            
            # Add filters dynamically
            for field, value in filters.items():
                # Handle numeric fields
                if field in ['population', 'rate', 'estimated_gdp']:
                    # Handle range queries with operators
                    if value.startswith('>='):
                        query += f" AND {field} >= %s"
                        params.append(float(value[2:]))
                    elif value.startswith('<='):
                        query += f" AND {field} <= %s"
                        params.append(float(value[2:]))
                    elif value.startswith('>'):
                        query += f" AND {field} > %s"
                        params.append(float(value[1:]))
                    elif value.startswith('<'):
                        query += f" AND {field} < %s"
                        params.append(float(value[1:]))
                    else:
                        query += f" AND {field} = %s"
                        params.append(float(value))
                # Handle text fields with LIKE for partial matches
                else:
                    query += f" AND {field} LIKE %s"
                    params.append(f"%{value}%")
            
            # Execute query with parameters
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            countries_df = pd.DataFrame(rows, columns=columns)
            connection.close()
            
            return jsonify(countries_df.to_dict(orient='records')), 200
        else:
            return jsonify({"error": "Failed to establish database connection"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/countries/<name>', methods=['GET'])
def get_country_by_name(name):
    try:
        # Fetch country data from the database
        connection = create_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute("USE countries_db")
            cursor.execute("SELECT * FROM countries WHERE name = %s", (name,))
            row = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            country_df = pd.DataFrame([row], columns=columns)
            connection.close()

            return jsonify(country_df.to_dict(orient='records')), 200
        else:
            return jsonify({"error": "Failed to establish database connection"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/countries/<name>', methods=['DELETE'])
def delete_country(name):
    try:
        # Delete country data from the database
        connection = create_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute("USE countries_db")
            cursor.execute("DELETE FROM countries WHERE name = %s", (name,))
            connection.commit()
            connection.close()

            return jsonify({"message": "Country deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to establish database connection"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/status', methods=['GET'])
def get_status():
    """
    Get the number of rows in the countries table and the last refresh timestamp.
    """
    try:
        connection = create_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute("USE countries_db")
            cursor.execute("SELECT COUNT(*) FROM countries")
            row_count = cursor.fetchone()[0]
            connection.close()

            return jsonify({"total_countries": row_count, "last_refreshed_at": last_refresh}), 200
        else:
            return jsonify({"error": "Failed to establish database connection"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/countries/image')
def get_country_image():
    """
    Returns all contents of the entire database.
    The fields are:
        id — auto-generated
        name — required
        capital — optional
        region — optional
        population — required
        currency_code — required
        exchange_rate — required
        estimated_gdp — computed from population × random(1000–2000) ÷ exchange_rate
        flag_url — optional
        last_refreshed_at — auto timestamp
    """
    try:
        connection = create_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute("USE countries_db")
            cursor.execute("SELECT * FROM countries")
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            countries_df = pd.DataFrame(rows, columns=columns)
            connection.close()

            return jsonify(countries_df.to_dict(orient='records')), 200
        else:
            return jsonify({"error": "Failed to establish database connection"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)