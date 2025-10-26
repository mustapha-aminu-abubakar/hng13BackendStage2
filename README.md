# Countries Information API

A Flask-based REST API that provides information about countries, including their population, currencies, and estimated GDP. The application fetches data from external APIs, stores it in a MySQL database, and provides various endpoints for accessing and visualizing the data.

## Features

- Real-time country data from REST Countries API
- Current currency exchange rates from Exchange Rate API
- MySQL database integration
- Data visualization through generated images
- Filtering capabilities for country data
- Automatic GDP estimation based on population and exchange rates

## Prerequisites

- Python 3.x
- MySQL Server
- Required Python packages (install using `pip install -r requirements.txt`):
  - Flask
  - pandas
  - mysql-connector-python
  - requests
  - Pillow
  - python-dotenv

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
MYSQLHOST=localhost
MYSQLUSER=your_username
MYSQLPASSWORD=your_password
MYSQLPORT=3306
```

## Database Schema

The application uses a MySQL database with the following schema:

```sql
CREATE TABLE countries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    capital VARCHAR(255),
    region VARCHAR(100),
    population BIGINT,
    flag VARCHAR(255),
    currency_code VARCHAR(10),
    rate DECIMAL(20,10),
    estimated_gdp DECIMAL(30,10),
    last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

## API Endpoints

### 1. Refresh Database Data
- **URL:** `/countries/refresh`
- **Method:** `POST`
- **Description:** Fetches fresh data from external APIs and updates the database
- **Response:** 
  ```json
  {
    "message": "Database populated successfully",
    "last_refresh": "2025-10-26T10:30:00Z"
  }
  ```

### 2. Get Countries
- **URL:** `/countries`
- **Method:** `GET`
- **Required Parameters:**
  - `name`: Country name (supports partial matches)
  - `population`: Population value (supports >, <, >=, <= operators)
  - `currency_code`: Currency code
- **Example:** `/countries?name=United&population=>1000000&currency_code=USD`
- **Response:** List of matching countries with their details

### 3. Get Country Statistics Image
- **URL:** `/countries/image`
- **Method:** `GET`
- **Description:** Generates and serves a PNG image containing:
  - Total number of countries
  - Top 5 countries by estimated GDP
  - Last database refresh timestamp
- **Response:** PNG image file

### 4. Get Status
- **URL:** `/status`
- **Method:** `GET`
- **Description:** Returns current database statistics
- **Response:**
  ```json
  {
    "total_countries": 195,
    "last_refreshed_at": "2025-10-26T10:30:00Z"
  }
  ```

## Project Structure

```
stage2/
│
├── app.py              # Main Flask application
├── create_db.py        # Database creation and population
├── prepare_data.py     # Data fetching and preparation
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
└── README.md          # Documentation
```

## Data Sources

- Country data: [REST Countries API](https://restcountries.com)
- Currency rates: [Exchange Rates API](https://open.er-api.com)

## Running the Application

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the MySQL database and environment variables

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. The API will be available at `http://localhost:5000`

## Error Handling

The API includes comprehensive error handling for:
- Database connection issues
- External API failures
- Invalid query parameters
- Missing required fields
- Data validation errors

## Sample API Usage

1. Refresh database:
```bash
curl -X POST http://localhost:5000/countries/refresh
```

2. Get filtered countries:
```bash
curl "http://localhost:5000/countries?name=United&population=>1000000&currency_code=USD"
```

3. Get statistics image:
```bash
curl http://localhost:5000/countries/image --output stats.png
```

4. Check status:
```bash
curl http://localhost:5000/status
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.