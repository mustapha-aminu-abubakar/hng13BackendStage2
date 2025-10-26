from flask import Flask, jsonify, request, send_file
import pandas as pd
from create_db import main, create_connection
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import io
import os
app = Flask(__name__)

last_refresh = None

def save_img():
    # Create database connection
    connection = create_connection()
    if connection is not None:
        cursor = connection.cursor()
        cursor.execute("USE countries_db")
        
        # Get total number of countries
        cursor.execute("SELECT COUNT(*) FROM countries")
        total_countries = cursor.fetchone()[0]
        
        # Get top 5 countries by estimated GDP (population * rate)
        cursor.execute("""
            SELECT name, population * rate as estimated_gdp 
            FROM countries 
            ORDER BY estimated_gdp DESC 
            LIMIT 5
        """)
        top_gdp_countries = cursor.fetchall()
        
        # Get timestamp of last refresh
        cursor.execute("""
            SELECT last_refreshed_at FROM countries LIMIT 1
        """)
        last_refresh_ts = cursor.fetchone()[0]
        # Create a new image with a white background
        width = 800
        height = 600
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to use Arial font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw title
        draw.text((50, 50), "Countries Database Statistics", fill='black', font=font)
        
        # Draw total countries
        draw.text((50, 120), f"Total Number of Countries: {total_countries}", fill='black', font=font)
        
        # Draw timestamp
        draw.text((50, 170), f"Last Database Refresh: {last_refresh_ts}", fill='black', font=font)
        
        # Draw top 5 GDP countries
        draw.text((50, 240), "Top 5 Countries by Estimated GDP:", fill='black', font=font)
        y = 290
        for i, (country, gdp) in enumerate(top_gdp_countries, 1):
            gdp_formatted = "{:,.2f}".format(gdp)
            draw.text((70, y), f"{i}. {country}: ${gdp_formatted}", fill='black', font=small_font)
            y += 40

        # Save image to file in cache directory
        image_path = "./cache/summary.png"
        image.save(image_path, 'PNG')

            
@app.route('/countries/refresh', methods=['POST']) 
def populate_db_route():
    global last_refresh 
    try:
        main()  # Call the main function from create_db.py to populate the database
        save_img()
        last_refresh = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return jsonify({"message": f"Database populated successfully at {last_refresh}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/countries', methods=['GET'])
def get_countries():
    try:
        filter_errors = {}
        # Get query parameters
        filters = request.args.to_dict()
        print(f'filters ------ {filters}')
        
        if 'name' not in filters: 
            filter_errors['name'] = 'is required'
        if 'population' not in filters:             
            filter_errors['population'] = 'is required'
        if 'currency_code' not in filters: 
            filter_errors['currency_code'] = 'is required'
  
        if filter_errors:
            return jsonify({"errors": "Validation failed", "details": filter_errors}), 400

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
            connection.close()
            if row:
                columns = [column[0] for column in cursor.description]
                country_df = pd.DataFrame([row], columns=columns)
                return jsonify(country_df.to_dict(orient='records')), 200
            else:
                return jsonify({"error": "Country not found"}), 404
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
    global last_refresh
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
    try:
        # Serve the pre-generated summary image from cache
        image_path = "./cache/summary.png
        print(image_path)
        if not os.path.exists(image_path):
            return jsonify({"error": "Summary image not found"}), 404

        return send_file(
            image_path,
            mimetype='image/png',
            as_attachment=False,
            download_name='summary.png'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/test', methods=['GET'])
# def test():
#     return jsonify({'message': 'Flask app connect successful'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)