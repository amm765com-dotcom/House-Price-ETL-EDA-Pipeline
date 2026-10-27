import sqlite3
from typing import Optional
import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
import seaborn as sns


# ==========================================
# 1. PYDANTIC MODEL FOR DATA VALIDATION
# ==========================================
class HousePropertyModel(BaseModel):
  area: float = Field(..., gt=0, description='Area must be a positive number')
  bedrooms: int = Field(
      ..., ge=0, description='Bedrooms must be a non-negative integer'
  )
  bathrooms: float = Field(..., ge=0)
  location: str = Field(..., min_length=1)
  property_type: str
  number_floors: Optional[int] = Field(default=1, ge=1)
  year_built: Optional[int] = Field(default=2000, ge=1800)
  price: float = Field(..., gt=0, description='Price must be a positive number')


# ==========================================
# 2. EXTRACT PHASE (Mock API Extraction)
# ==========================================
def extract_data():
  print('--- [EXTRACT] Fetching raw data from API ---')

  raw_api_data = [
      {
          'area': 1200.5,
          'bedrooms': 3,
          'bathrooms': 2.0,
          'location': 'Gulberg',
          'property_type': 'House',
          'number_floors': 2,
          'year_built': 2018,
          'price': 15500000.0,
      },
      {
          'area': 850.0,
          'bedrooms': 2,
          'bathrooms': 1.0,
          'location': 'DHA',
          'property_type': 'Apartment',
          'number_floors': 1,
          'year_built': 2020,
          'price': 9000000.0,
      },
      {
          'area': 1200.5,
          'bedrooms': 3,
          'bathrooms': 2.0,
          'location': 'Gulberg',
          'property_type': 'House',
          'number_floors': 2,
          'year_built': 2018,
          'price': 15500000.0,
      },  # Duplicate record
      {
          'area': -500.0,
          'bedrooms': 4,
          'bathrooms': 3.0,
          'location': 'Model Town',
          'property_type': 'House',
          'number_floors': 2,
          'year_built': 2015,
          'price': -20000.0,
      },  # Invalid data
      {
          'area': None,
          'bedrooms': 4,
          'bathrooms': 3.0,
          'location': 'Bahria Town',
          'property_type': 'Villa',
          'number_floors': 2,
          'year_built': 2021,
          'price': 22000000.0,
      },  # Missing value
  ]

  return pd.DataFrame(raw_api_data)


# ==========================================
# 3. TRANSFORM PHASE (Pandas Cleaning)
# ==========================================
def transform_data(df):
  print('--- [TRANSFORM] Cleaning data using Pandas ---')
  initial_count = len(df)

  df = df.dropna(subset=['area', 'price', 'bedrooms', 'location'])
  df = df.drop_duplicates()

  df['location'] = df['location'].str.strip().str.title()
  df['property_type'] = df['property_type'].str.strip().str.title()

  print(
      f'Cleaned records count: {len(df)} (Removed {initial_count - len(df)}'
      ' rows)'
  )
  return df


# ==========================================
# 4. VALIDATE PHASE (Pydantic Validation)
# ==========================================
def validate_data(df):
  print('--- [VALIDATE] Validating records using Pydantic ---')
  valid_records = []

  for index, row in df.iterrows():
    try:
      validated_row = HousePropertyModel(**row.to_dict())
      valid_records.append(validated_row.model_dump())
    except ValidationError as e:
      print(f'Validation failed for row {index}: {e.errors()}')

  print(f'Successfully validated {len(valid_records)} records.')
  return pd.DataFrame(valid_records)


# ==========================================
# 5. LOAD PHASE (Database Storage)
# ==========================================
def load_data(df):
  print('--- [LOAD] Loading validated data into Database ---')
  conn = sqlite3.connect('house_prices.db')
  df.to_sql('properties', conn, if_exists='replace', index=False)
  conn.close()
  print("Data successfully loaded into 'house_prices.db' under table 'properties'!")


# ==========================================
# 6. EDA PHASE (Exploratory Data Analysis)
# ==========================================
def perform_eda():
  print('\n--- [EDA] Starting Exploratory Data Analysis ---')

  conn = sqlite3.connect('house_prices.db')
  df = pd.read_sql('SELECT * FROM properties', conn)
  conn.close()

  if df.empty:
    print('No data available in database for EDA.')
    return

  # Descriptive Statistics
  print('\n--- Descriptive Statistics ---')
  print(df.describe())

  # Correlation Analysis
  print('\n--- Correlation with Price ---')
  numeric_df = df.select_dtypes(include=['number'])
  correlation = numeric_df.corr()['price'].sort_values(ascending=False)
  print(correlation)

  # Visualizations
  sns.set_theme(style='whitegrid')
  plt.figure(figsize=(14, 6))

  # Plot 1: Price Distribution
  plt.subplot(1, 2, 1)
  sns.histplot(df['price'], kde=True, color='blue')
  plt.title('House Price Distribution')
  plt.xlabel('Price')
  plt.ylabel('Frequency')

  # Plot 2: Area vs Price
  plt.subplot(1, 2, 2)
  sns.scatterplot(x='area', y='price', data=df, hue='bedrooms', palette='viridis')
  plt.title('House Area vs Price')
  plt.xlabel('Area')
  plt.ylabel('Price')

  plt.tight_layout()
  plt.show()
  print('\nEDA Completed Successfully! Visualizations generated.')


# ==========================================
# PIPELINE EXECUTION
# ==========================================
if __name__ == '__main__':
  print('Starting Complete ETL & EDA Pipeline Execution...\n')

  raw_df = extract_data()
  transformed_df = transform_data(raw_df)
  validated_df = validate_data(transformed_df)

  if not validated_df.empty:
    load_data(validated_df)
    # Yahan EDA function call kiya gaya hai load hone ke baad
    perform_eda()
  else:
    print('No valid data available to load.')

  print('\nPipeline Completed Successfully!')