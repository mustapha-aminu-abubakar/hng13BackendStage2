import pandas as pd
import requests
import random

COUNTRIES_URL = 'https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies'
CURRENCIES_URL = 'https://open.er-api.com/v6/latest/USD'

def fetch_countries_data(url=COUNTRIES_URL):
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        print("Data retrieved successfully.")
        print(data)
    else:
        print(f"Error retrieving data: {response.status_code}")
        data = None # Set data to None in case of an error
    return data

def fetch_currencies_data(): 
    response_currency = requests.get(CURRENCIES_URL)

    # Check if the request was successful
    if response_currency.status_code == 200:
        currency_data = response_currency.json()
        print("Currency data retrieved successfully.")
    else:
        print(f"Error retrieving currency data: {response_currency.status_code}")
        currency_data = None # Set currency_data to None in case of an error
    return currency_data

def clean_countries_data(data):
    data_clean = []
    if data:
        for country in data:
            entry = {**country}
            # Check if 'currencies' key exists and is not empty
            if 'currencies' in country and country['currencies']:
                entry['currency'] = country['currencies'][0]['code']
                del entry['currencies'] # Remove the 'currencies' key from the entry
            else:
                entry['currency'] = None # Or some other appropriate value indicating no currency data
            data_clean.append(entry)
        return data_clean
    else: return None

def currencies_df(currency_data):
    if currency_data:  # Check if currency_data is not None
        currency_df = pd.DataFrame.from_dict(currency_data['rates'], orient='index', columns=['rate'])
        currency_df.index.name = 'currency'
        return currency_df
    else:
        print("No currency data available to convert to DataFrame.")
        return pd.DataFrame()  # Return an empty DataFrame
    
def countries_df(data_clean):
    if data_clean is None:
        print("No country data available to convert to DataFrame.")
        return pd.DataFrame()  # Return an empty DataFrame
    countries_df = pd.DataFrame(data_clean)
    return countries_df

def main():
    countries_data = fetch_countries_data()
    currency_data = fetch_currencies_data()

    if countries_data and currency_data:
        data_clean = clean_countries_data(countries_data)
        countries_dataframe = countries_df(data_clean)
        print("Countries DataFrame:")
        print(countries_dataframe.head())

        currency_dataframe = currencies_df(currency_data)
        print("Currencies DataFrame:")
        print(currency_dataframe.head())
    
    else: 
        return {"COUNTRIES_URL": countries_data, "CURRENCIES_URL": currency_data}
    
    merged_df = pd.merge(countries_dataframe, currency_dataframe, on='currency', how='left')
    merged_df['estimated_gdp'] = merged_df['population'] * random.randint(1000, 2000) / merged_df['rate'] 
    print(merged_df.head())
    
    return merged_df

if __name__ == "__main__":
    main()