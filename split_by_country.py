#!/usr/bin/env python3
"""
Script to split the main administrative data file into separate Excel files for each country.
"""

import pandas as pd
from pathlib import Path
import sys

def split_data_by_country():
    """Reads the main Excel file and creates a separate file for each country."""
    
    input_file = 'Complete_Administrative_Divisions_with_Coordinates.xlsx'
    output_dir = Path('Country_Exports')
    
    print(f"Reading main data file: {input_file}")
    
    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        print("Please run the main processing script first to generate it.")
        sys.exit(1)
        
    # Create the output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Get a list of unique countries
    countries = df['Country_Name'].unique()
    
    print(f"Found {len(countries)} countries. Exporting each to a separate file...")
    
    for country in countries:
        if pd.isna(country):
            continue
            
        # Sanitize the country name to create a valid filename
        safe_filename = "".join([c for c in country if c.isalpha() or c.isdigit() or c.isspace()]).rstrip()
        output_file = output_dir / f"{safe_filename}.xlsx"
        
        print(f"  -> Processing: {country}")
        
        country_df = df[df['Country_Name'] == country]
        
        # Write to a new Excel file
        country_df.to_excel(output_file, index=False, engine='openpyxl')
        
    print(f"\nSuccess! All country files have been exported to the '{output_dir}' directory.")

if __name__ == "__main__":
    split_data_by_country()
