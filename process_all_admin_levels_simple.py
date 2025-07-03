#!/usr/bin/env python3
"""
Comprehensive script to extract all administrative levels with coordinates.
This script processes the GNS (GEOnet Names Server) data files to extract:
- All administrative levels (ADM1, ADM2, ADM3, ADM4)
- Coordinates (latitude, longitude) for each administrative division
- Country information and hierarchical relationships
"""

import pandas as pd
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def process_gns_administrative_data():
    """Process GNS administrative data with coordinates."""
    
    print("Processing GNS Administrative Data with Coordinates")
    print("=" * 55)
    
    try:
        print("1. Reading country codes...")
        countries_df = pd.read_csv('Country_Codes.csv')
        print(f"   Found {len(countries_df)} countries")
        
        print("\n2. Reading administrative regions data...")
        print("   This may take a while due to large file size...")
        
        # Read the large administrative regions file with all relevant columns
        admin_df = pd.read_csv(
            'Administrative_Regions/Administrative_Regions.txt',
            sep='\t',
            low_memory=False
        )
        
        print(f"   Loaded {len(admin_df)} total records")
        print(f"   Columns available: {len(admin_df.columns)}")
        
        print("\n3. Filtering for administrative divisions...")
        
        # Filter for administrative divisions (ADM1, ADM2, ADM3, ADM4, ADMD)
        adm_mask = admin_df['desig_cd'].str.startswith(('ADM1', 'ADM2', 'ADM3', 'ADM4', 'ADMD'), na=False)
        admin_filtered = admin_df[adm_mask].copy()
        
        print(f"   Administrative records found: {len(admin_filtered):,}")
        
        # Check what designation codes we have
        print("\n   Administrative levels found:")
        level_counts = admin_filtered['desig_cd'].value_counts()
        for level, count in level_counts.head(10).items():
            print(f"     {level}: {count:,} records")
        
        print("\n4. Applying quality filters...")
        
        # Filter for records with display values (not empty)
        if 'display' in admin_filtered.columns:
            display_mask = admin_filtered['display'].notna() & (admin_filtered['display'] != '')
            admin_filtered = admin_filtered[display_mask]
            print(f"   After display filter: {len(admin_filtered):,}")
        
        # Remove records without coordinates
        coord_mask = (pd.to_numeric(admin_filtered['lat_dd'], errors='coerce').notna() & 
                     pd.to_numeric(admin_filtered['long_dd'], errors='coerce').notna())
        admin_filtered = admin_filtered[coord_mask]
        print(f"   After coordinate filter: {len(admin_filtered):,}")
        
        print("\n5. Applying deduplication strategy...")
        print("   Priority: Approved (N) > Conventional (C) > Non-auth (D) > Variant (V)")
        print("   Secondary: Lower name_rank > English language > others")
        
        # Set up priority scoring
        name_type_priority = {'N': 1, 'C': 2, 'D': 3, 'V': 4}
        admin_filtered['nt_priority'] = admin_filtered['nt'].map(name_type_priority).fillna(999)
        
        # Convert name_rank to numeric (lower is better)
        admin_filtered['name_rank_num'] = pd.to_numeric(admin_filtered['name_rank'], errors='coerce').fillna(999)
        
        # Language priority: English first, then others
        admin_filtered['lang_priority'] = admin_filtered['lang_cd'].apply(
            lambda x: 1 if x == 'eng' else 2
        )
        
        # Sort by quality criteria to get best records first
        admin_filtered = admin_filtered.sort_values([
            'ufi',                # Group by unique feature ID
            'nt_priority',        # Name type priority (N=1, C=2, D=3, V=4)
            'name_rank_num',      # Name rank (lower is better)
            'lang_priority'       # Language priority (eng=1, others=2)
        ])
        
        # Keep only the first (best) record for each unique feature
        admin_deduplicated = admin_filtered.groupby('ufi').first().reset_index()
        
        print(f"   After deduplication: {len(admin_deduplicated):,} unique divisions")
        
        # Count by administrative level after deduplication
        final_level_counts = admin_deduplicated['desig_cd'].value_counts()
        print("\n   Final counts by administrative level:")
        for level, count in final_level_counts.items():
            if level.startswith('ADM'):
                print(f"     {level}: {count:,} unique divisions")
        
        print("\n6. Processing coordinates and country information...")
        
        # Clean coordinates
        admin_deduplicated['latitude'] = pd.to_numeric(admin_deduplicated['lat_dd'], errors='coerce')
        admin_deduplicated['longitude'] = pd.to_numeric(admin_deduplicated['long_dd'], errors='coerce')
        
        # Merge with country information
        admin_coords = admin_deduplicated.merge(
            countries_df[['Country_Code', 'Short_Name', 'Full_Name']], 
            left_on='cc_ft', 
            right_on='Country_Code', 
            how='left',
            suffixes=('', '_country')
        )
        
        print(f"   Records with country info: {len(admin_coords)}")
        
        print("\n7. Creating structured output...")
        
        # Create the final output dataframe
        output_df = admin_coords[[
            'Country_Code', 'Short_Name', 'Full_Name',
            'desig_cd', 'full_name', 'adm1',
            'latitude', 'longitude',
            'ufi', 'uni', 'nt', 'name_rank', 'lang_cd',
            'transl_cd', 'script_cd', 'generic'
        ]].copy()
        
        # Rename columns for clarity
        output_df = output_df.rename(columns={
            'Short_Name': 'Country_Name',
            'Full_Name': 'Country_Full_Name',
            'desig_cd': 'Administrative_Level',
            'full_name': 'Administrative_Name',
            'adm1': 'ADM1_Code',
            'ufi': 'Unique_Feature_ID',
            'uni': 'Unique_Name_ID',
            'nt': 'Name_Type',
            'name_rank': 'Name_Rank',
            'lang_cd': 'Language_Code',
            'transl_cd': 'Transliteration_Code',
            'script_cd': 'Script_Code',
            'generic': 'Generic_Term'
        })
        
        # Sort by country, then administrative level, then name
        output_df = output_df.sort_values([
            'Country_Name', 
            'Administrative_Level', 
            'Administrative_Name'
        ])
        
        print("\n8. Creating Excel output with multiple sheets...")
        
        output_file = 'Complete_Administrative_Divisions_with_Coordinates.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # All administrative divisions
            output_df.to_excel(writer, sheet_name='All_Admin_Divisions', index=False)
            
            # Separate sheets by administrative level
            for level in ['ADM1', 'ADM2', 'ADM3', 'ADM4', 'ADMD']:
                level_data = output_df[output_df['Administrative_Level'] == level]
                if not level_data.empty:
                    sheet_name = f'{level}_Divisions'
                    level_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Country summary
            country_summary = output_df.groupby([
                'Country_Code', 'Country_Name', 'Administrative_Level'
            ]).size().reset_index(name='Count')
            
            country_pivot = country_summary.pivot(
                index=['Country_Code', 'Country_Name'], 
                columns='Administrative_Level', 
                values='Count'
            ).fillna(0).astype(int)
            
            # Add total column
            country_pivot['Total'] = country_pivot.sum(axis=1)
            country_pivot = country_pivot.sort_values('Total', ascending=False)
            
            country_pivot.to_excel(writer, sheet_name='Country_Summary')
            
            # Top countries by total administrative divisions
            top_countries = country_pivot.head(30).copy()
            top_countries.to_excel(writer, sheet_name='Top_30_Countries')
        
        print(f"\n✅ SUCCESS! Created {output_file}")
        print("\nFile contains the following sheets:")
        print("  📊 All_Admin_Divisions: Complete dataset with coordinates")
        print("  📍 ADM1_Divisions: First-order divisions (states/provinces)")  
        print("  📍 ADM2_Divisions: Second-order divisions (counties/districts)")
        print("  📍 ADM3_Divisions: Third-order divisions (municipalities)")
        print("  📍 ADM4_Divisions: Fourth-order divisions (local areas)")
        print("  📍 ADMD_Divisions: General administrative divisions")
        print("  📈 Country_Summary: Administrative divisions by country and level")
        print("  🏆 Top_30_Countries: Countries with most administrative divisions")
        
        # Display summary statistics
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total administrative divisions: {len(output_df):,}")
        print(f"   Countries represented: {output_df['Country_Code'].nunique()}")
        print(f"   Administrative levels: {output_df['Administrative_Level'].nunique()}")
        
        print(f"\n📍 BY ADMINISTRATIVE LEVEL:")
        level_summary = output_df['Administrative_Level'].value_counts().sort_index()
        for level, count in level_summary.items():
            print(f"   {level}: {count:,} divisions")
        
        print(f"\n🌍 TOP 10 COUNTRIES BY TOTAL DIVISIONS:")
        top_10 = country_pivot.head(10)
        for idx, (country_info, row) in enumerate(top_10.iterrows(), 1):
            country_code, country_name = country_info
            print(f"   {idx:2d}. {country_name} ({country_code}): {row['Total']:,} divisions")
        
        # Show sample of the data
        print(f"\n📋 SAMPLE DATA (first 5 records):")
        sample_df = output_df.head(5)[['Country_Name', 'Administrative_Level', 'Administrative_Name', 'latitude', 'longitude']]
        for _, row in sample_df.iterrows():
            print(f"   {row['Country_Name']}: {row['Administrative_Name']} ({row['Administrative_Level']}) - {row['latitude']:.4f}, {row['longitude']:.4f}")
        
        print(f"\n📋 DATA QUALITY INFORMATION:")
        print(f"   Deduplication applied: One record per unique geographic feature")
        print(f"   Name selection: Official/approved names preferred")
        print(f"   Display filter: Only public-display records included")
        print(f"   Coordinate coverage: 100% (filtered for valid coordinates)")
        
        return output_file
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find required file - {e}")
        print("Make sure the following files exist:")
        print("  - Country_Codes.csv")
        print("  - Administrative_Regions/Administrative_Regions.txt")
        return None
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🌍 GNS Administrative Data Processor with Coordinates")
    print("=" * 55)
    print("This script will process the complete GNS dataset to extract:")
    print("• All administrative levels (ADM1, ADM2, ADM3, ADM4)")  
    print("• Coordinates (latitude, longitude) for each division")
    print("• Country information and hierarchical relationships")
    print("• Intelligent deduplication with quality name selection")
    print()
    
    # Process the main administrative data
    output_file = process_gns_administrative_data()
    
    if output_file:
        print(f"\n🎉 Processing complete!")
        print(f"📁 Main output: {output_file}")
        print(f"\n📖 The Excel file contains multiple sheets with administrative divisions at all levels.")
        print(f"📖 Each division includes precise latitude/longitude coordinates.")
        print(f"📖 Data has been deduplicated to show the best/official name for each location.")
        
    else:
        print("❌ Processing failed")
        sys.exit(1)
