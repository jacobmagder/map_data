#!/usr/bin/env python3
"""
Script to process country subdivision data and export to Excel format.
This script reads the ADM1_Codes.csv file containing administrative subdivisions
and merges it with country information to create a comprehensive Excel report.
"""

import pandas as pd
import sys
from pathlib import Path

def process_subdivisions():
    """Process subdivision data and create Excel output."""
    
    try:
        # Read the subdivision data
        print("Reading subdivision data...")
        subdivisions_df = pd.read_csv('ADM1_Codes.csv')
        print(f"Found {len(subdivisions_df)} subdivisions")
        
        # Read country data for additional context
        print("Reading country data...")
        countries_df = pd.read_csv('Country_Codes.csv')
        print(f"Found {len(countries_df)} countries")
        
        # Merge subdivision data with country information
        print("Merging data...")
        merged_df = subdivisions_df.merge(
            countries_df[['Country_Code', 'Short_Name', 'Full_Name']], 
            on='Country_Code', 
            how='left',
            suffixes=('_Subdivision', '_Country')
        )
        
        # Rename columns for clarity
        merged_df = merged_df.rename(columns={
            'Name': 'Subdivision_Name',
            'Short_Name': 'Country_Short_Name',
            'Full_Name': 'Country_Full_Name',
            'First_Order_Administrative_Subdivision_Code': 'Subdivision_Code'
        })
        
        # Reorder columns for better readability
        column_order = [
            'Country_Code',
            'Country_Short_Name', 
            'Country_Full_Name',
            'Subdivision_Code',
            'Subdivision_Name',
            'GENC_Short_URN_based_Identifier'
        ]
        merged_df = merged_df[column_order]
        
        # Filter out general entries (those ending with -000)
        print("Filtering data...")
        specific_subdivisions = merged_df[~merged_df['Subdivision_Code'].str.endswith('-000')]
        general_entries = merged_df[merged_df['Subdivision_Code'].str.endswith('-000')]
        
        print(f"Specific subdivisions: {len(specific_subdivisions)}")
        print(f"General entries: {len(general_entries)}")
        
        # Create Excel file with multiple sheets
        output_file = 'Country_Subdivisions.xlsx'
        print(f"Creating Excel file: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # All subdivisions
            merged_df.to_excel(writer, sheet_name='All_Subdivisions', index=False)
            
            # Only specific subdivisions (excluding general entries)
            specific_subdivisions.to_excel(writer, sheet_name='Specific_Subdivisions', index=False)
            
            # Summary by country
            country_summary = specific_subdivisions.groupby(['Country_Code', 'Country_Short_Name']).size().reset_index(name='Number_of_Subdivisions')
            country_summary = country_summary.sort_values('Number_of_Subdivisions', ascending=False)
            country_summary.to_excel(writer, sheet_name='Country_Summary', index=False)
            
            # Countries with most subdivisions (top 20)
            top_countries = country_summary.head(20)
            top_countries.to_excel(writer, sheet_name='Top_20_Countries', index=False)
        
        print(f"\nSuccess! Created {output_file} with the following sheets:")
        print("- All_Subdivisions: Complete dataset with all entries")
        print("- Specific_Subdivisions: Only actual subdivisions (excluding general entries)")
        print("- Country_Summary: Number of subdivisions per country")
        print("- Top_20_Countries: Countries with the most subdivisions")
        
        # Display some statistics
        print(f"\nData Statistics:")
        print(f"Total entries: {len(merged_df)}")
        print(f"Specific subdivisions: {len(specific_subdivisions)}")
        print(f"Countries represented: {merged_df['Country_Code'].nunique()}")
        
        # Show top 10 countries by subdivision count
        print(f"\nTop 10 countries by number of subdivisions:")
        for idx, row in country_summary.head(10).iterrows():
            print(f"  {row['Country_Short_Name']}: {row['Number_of_Subdivisions']} subdivisions")
            
        return output_file
        
    except FileNotFoundError as e:
        print(f"Error: Could not find required file - {e}")
        print("Make sure ADM1_Codes.csv and Country_Codes.csv are in the current directory")
        return None
    except Exception as e:
        print(f"Error processing data: {e}")
        return None

if __name__ == "__main__":
    output_file = process_subdivisions()
    if output_file:
        print(f"\nDone! Your subdivision data is now available in {output_file}")
    else:
        print("Failed to process subdivision data")
        sys.exit(1)
