#!/usr/bin/env python3
"""
Interactive script to query subdivisions for specific countries.
Usage: python query_subdivisions.py [country_code_or_name]
"""

import pandas as pd
import sys

def load_data():
    """Load subdivision and country data."""
    try:
        subdivisions_df = pd.read_csv('ADM1_Codes.csv')
        countries_df = pd.read_csv('Country_Codes.csv')
        
        # Merge the data
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
        
        return merged_df
    except FileNotFoundError as e:
        print(f"Error: Could not find required file - {e}")
        return None

def search_country(df, query):
    """Search for a country by code or name."""
    query_upper = query.upper()
    
    # Search by country code
    country_code_match = df[df['Country_Code'] == query_upper]
    if not country_code_match.empty:
        return country_code_match
    
    # Search by country name (case insensitive)
    name_match = df[df['Country_Short_Name'].str.upper().str.contains(query_upper, na=False)]
    if not name_match.empty:
        return name_match
    
    # Search by full country name
    full_name_match = df[df['Country_Full_Name'].str.upper().str.contains(query_upper, na=False)]
    if not full_name_match.empty:
        return full_name_match
    
    return pd.DataFrame()

def main():
    """Main function to handle user queries."""
    df = load_data()
    if df is None:
        sys.exit(1)
    
    if len(sys.argv) > 1:
        # Command line argument provided
        query = ' '.join(sys.argv[1:])
        results = search_country(df, query)
        
        if results.empty:
            print(f"No country found matching '{query}'")
            return
        
        # Filter out general entries
        specific_subdivisions = results[~results['Subdivision_Code'].str.endswith('-000')]
        
        if specific_subdivisions.empty:
            print(f"No subdivisions found for '{query}'")
            return
        
        country_name = specific_subdivisions.iloc[0]['Country_Short_Name']
        print(f"\nSubdivisions for {country_name}:")
        print("=" * (len(country_name) + 17))
        
        for _, row in specific_subdivisions.iterrows():
            print(f"  {row['Subdivision_Code']}: {row['Subdivision_Name']}")
        
        print(f"\nTotal subdivisions: {len(specific_subdivisions)}")
        
    else:
        # Interactive mode
        print("Country Subdivision Query Tool")
        print("=" * 30)
        print("Enter a country code (e.g., 'USA') or country name (e.g., 'United States')")
        print("Type 'quit' to exit\n")
        
        while True:
            query = input("Enter country: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            results = search_country(df, query)
            
            if results.empty:
                print(f"No country found matching '{query}'. Try a different search term.\n")
                continue
            
            # Show matching countries if multiple found
            unique_countries = results[['Country_Code', 'Country_Short_Name']].drop_duplicates()
            if len(unique_countries) > 1:
                print(f"\nMultiple countries found:")
                for _, country in unique_countries.iterrows():
                    print(f"  {country['Country_Code']}: {country['Country_Short_Name']}")
                print("Please be more specific.\n")
                continue
            
            # Filter out general entries
            specific_subdivisions = results[~results['Subdivision_Code'].str.endswith('-000')]
            
            if specific_subdivisions.empty:
                print(f"No subdivisions found for '{query}'\n")
                continue
            
            country_name = specific_subdivisions.iloc[0]['Country_Short_Name']
            print(f"\nSubdivisions for {country_name}:")
            print("=" * (len(country_name) + 17))
            
            for _, row in specific_subdivisions.iterrows():
                print(f"  {row['Subdivision_Code']}: {row['Subdivision_Name']}")
            
            print(f"\nTotal subdivisions: {len(specific_subdivisions)}\n")

if __name__ == "__main__":
    main()
