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
        admin_columns = [
            'rk', 'ufi', 'uni', 'full_name', 'nt', 'lat_dd', 'long_dd', 
            'efctv_dt', 'term_dt_f', 'term_dt_n', 'desig_cd', 'fc', 'cc_ft', 'adm1',
            'name_rank', 'lang_cd', 'transl_cd', 'script_cd', 'display', 'generic'
        ]
        
        admin_df = pd.read_csv(
            'Administrative_Regions/Administrative_Regions.txt',
            sep='\t',
            usecols=admin_columns,
            low_memory=False
        )
        
        print(f"   Loaded {len(admin_df)} administrative records")
        
        print("\n3. Filtering and deduplicating administrative divisions...")
        
        # Filter for administrative divisions (ADM1, ADM2, ADM3, ADM4, ADMD)
        adm_mask = admin_df['desig_cd'].str.startswith(('ADM1', 'ADM2', 'ADM3', 'ADM4', 'ADMD'), na=False)
        admin_filtered = admin_df[adm_mask].copy()
        
        print(f"   Initial administrative records: {len(admin_filtered):,}")
        
        # Filter for quality records
        print("   Applying quality filters...")
        
        # 1. Only include records marked for display
        if 'display' in admin_filtered.columns:
            display_mask = admin_filtered['display'].fillna('').str.upper() == 'Y'
            admin_filtered = admin_filtered[display_mask]
            print(f"   After display filter: {len(admin_filtered):,}")
        
        # 2. Apply display filter first - only show records marked for public display
        if 'display' in admin_filtered.columns:
            # Check what values exist in display column
            display_values = admin_filtered['display'].value_counts()
            print(f"   Display field sample values: {dict(list(display_values.items())[:5])}")
            
            # Filter for records that have display values (non-empty)
            # Display field contains comma-separated numbers indicating display contexts
            display_mask = admin_filtered['display'].notna() & (admin_filtered['display'] != '')
            admin_filtered = admin_filtered[display_mask]
            print(f"   After display filter: {len(admin_filtered):,}")
        
        # 3. Prefer official names based on Name Type (nt)
        # Priority: N (Approved/Official) > C (Conventional) > D (Non-authoritative) > V (Variant)
        name_type_priority = {'N': 1, 'C': 2, 'D': 3, 'V': 4}
        admin_filtered['nt_priority'] = admin_filtered['nt'].map(name_type_priority).fillna(999)
        
        # 4. Use name_rank to get primary names (lower rank = higher priority)
        admin_filtered['name_rank_num'] = pd.to_numeric(admin_filtered['name_rank'], errors='coerce').fillna(999)
        
        # 5. Language priority: English > common local languages > others
        # Priority: English (eng) = 1, common locals = 2, others = 3
        common_local_langs = {'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'ara', 'zho', 'jpn', 'hin'}
        admin_filtered['lang_priority'] = admin_filtered['lang_cd'].apply(
            lambda x: 1 if x == 'eng' else (2 if x in common_local_langs else 3)
        )
        
        # Remove records without coordinates
        coord_mask = (pd.to_numeric(admin_filtered['lat_dd'], errors='coerce').notna() & 
                     pd.to_numeric(admin_filtered['long_dd'], errors='coerce').notna())
        admin_filtered = admin_filtered[coord_mask]
        print(f"   After coordinate filter: {len(admin_filtered):,}")
        
        # Deduplicate: for each unique feature (ufi), keep the best name
        print("   Applying deduplication strategy...")
        print("   Priority: Approved (N) > Conventional (C) > Non-auth (D) > Variant (V)")
        print("   Secondary: Lower name_rank > English language > others")
        
        # Sort by quality criteria to get best records first
        admin_filtered = admin_filtered.sort_values([
            'ufi',                # Group by unique feature
            'nt_priority',        # Name type priority (N=1, C=2, D=3, V=4)
            'name_rank_num',      # Name rank (lower is better)
            'lang_priority'       # Language priority (eng=1, others=2)
        ])
        
        # Keep only the first (best) record for each unique feature
        admin_deduplicated = admin_filtered.groupby('ufi').first().reset_index()
        
        print(f"   After deduplication: {len(admin_deduplicated):,} unique divisions")
        
        # Count by administrative level
        level_counts = admin_deduplicated['desig_cd'].value_counts()
        for level, count in level_counts.items():
            if level.startswith('ADM'):
                print(f"     {level}: {count:,} divisions")
        
        print("\n4. Processing coordinates and country information...")
        
        # Clean and process the data
        admin_deduplicated['latitude'] = pd.to_numeric(admin_deduplicated['lat_dd'], errors='coerce')
        admin_deduplicated['longitude'] = pd.to_numeric(admin_deduplicated['long_dd'], errors='coerce')
        
        # Final coordinate check (should be minimal after earlier filtering)
        coord_mask = admin_deduplicated['latitude'].notna() & admin_deduplicated['longitude'].notna()
        admin_coords = admin_deduplicated[coord_mask].copy()
        
        print(f"   Final dataset: {len(admin_coords)} divisions with coordinates")
        
        # Merge with country information
        admin_coords = admin_coords.merge(
            countries_df[['Country_Code', 'Short_Name', 'Full_Name']], 
            left_on='cc_ft', 
            right_on='Country_Code', 
            how='left',
            suffixes=('', '_country')
        )
        
        print("\n5. Creating structured output...")
        
        # Rename columns for clarity
        output_df = admin_coords.rename(columns={
            'full_name': 'Administrative_Name',
            'desig_cd': 'Administrative_Level',
            'cc_ft': 'Country_Code_Original',
            'Country_Code': 'Country_Code',
            'Short_Name': 'Country_Name',  
            'Full_Name': 'Country_Full_Name',
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
        
        # Use the merged country code
        output_df['Country_Code'] = output_df['Country_Code']
        
        # Select and reorder columns
        final_columns = [
            'Country_Code',
            'Country_Name',
            'Country_Full_Name', 
            'Administrative_Level',
            'Administrative_Name',
            'ADM1_Code',
            'latitude',
            'longitude',
            'Unique_Feature_ID',
            'Unique_Name_ID',
            'Name_Type',
            'Name_Rank',
            'Language_Code',
            'Transliteration_Code',
            'Script_Code',
            'Generic_Term'
        ]
        
        output_df = output_df[final_columns]
        
        # Sort by country, then administrative level, then name
        output_df = output_df.sort_values([
            'Country_Name', 
            'Administrative_Level', 
            'Administrative_Name'
        ])
        
        print("\n6. Creating Excel output with multiple sheets...")
        
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
        
        print(f"\n📋 COORDINATE COVERAGE:")
        coord_coverage = (len(admin_coords) / len(admin_filtered)) * 100
        print(f"   {coord_coverage:.1f}% of administrative divisions have coordinates")
        
        print(f"\n📋 DATA QUALITY INFORMATION:")
        print(f"   Deduplication applied: One record per unique geographic feature")
        print(f"   Name selection: Official conventional names preferred")
        print(f"   Display filter: Only public-display records included")
        print(f"   See DATA_QUALITY_INFO.md for detailed filtering criteria")
        
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

def create_coordinate_lookup_tool():
    """Create a tool to quickly look up coordinates for administrative divisions."""
    
    lookup_script = '''#!/usr/bin/env python3
"""
Quick lookup tool for administrative division coordinates.
Usage: python3 coordinate_lookup.py [country_code] [admin_level]
"""

import pandas as pd
import sys

def load_admin_data():
    """Load the processed administrative data."""
    try:
        df = pd.read_excel('Complete_Administrative_Divisions_with_Coordinates.xlsx', 
                          sheet_name='All_Admin_Divisions')
        return df
    except FileNotFoundError:
        print("Error: Complete_Administrative_Divisions_with_Coordinates.xlsx not found")
        print("Please run the main processing script first.")
        return None

def search_divisions(df, country_code=None, admin_level=None, name_filter=None):
    """Search for administrative divisions."""
    result = df.copy()
    
    if country_code:
        result = result[result['Country_Code'].str.upper() == country_code.upper()]
    
    if admin_level:
        result = result[result['Administrative_Level'].str.upper() == admin_level.upper()]
    
    if name_filter:
        result = result[result['Administrative_Name'].str.contains(name_filter, case=False, na=False)]
    
    return result

def main():
    """Main function for coordinate lookup."""
    df = load_admin_data()
    if df is None:
        sys.exit(1)
    
    if len(sys.argv) == 1:
        # Interactive mode
        print("Administrative Division Coordinate Lookup")
        print("=" * 40)
        print("Available commands:")
        print("  country <CODE>     - Show all divisions for a country")
        print("  level <LEVEL>      - Show divisions by level (ADM1, ADM2, etc.)")
        print("  search <NAME>      - Search divisions by name")
        print("  stats              - Show statistics")
        print("  quit               - Exit")
        print()
        
        while True:
            try:
                cmd = input("Enter command: ").strip().split()
                if not cmd:
                    continue
                
                if cmd[0].lower() in ['quit', 'exit', 'q']:
                    break
                
                elif cmd[0].lower() == 'country' and len(cmd) > 1:
                    results = search_divisions(df, country_code=cmd[1])
                    if results.empty:
                        print(f"No divisions found for country code: {cmd[1]}")
                    else:
                        print(f"\\nDivisions for {results.iloc[0]['Country_Name']} ({cmd[1].upper()}):")
                        for _, row in results.iterrows():
                            print(f"  {row['Administrative_Level']}: {row['Administrative_Name']} "
                                  f"({row['latitude']:.4f}, {row['longitude']:.4f})")
                
                elif cmd[0].lower() == 'level' and len(cmd) > 1:
                    results = search_divisions(df, admin_level=cmd[1])
                    if results.empty:
                        print(f"No divisions found for level: {cmd[1]}")
                    else:
                        print(f"\\n{cmd[1].upper()} divisions (showing first 20):")
                        for _, row in results.head(20).iterrows():
                            print(f"  {row['Country_Name']}: {row['Administrative_Name']} "
                                  f"({row['latitude']:.4f}, {row['longitude']:.4f})")
                
                elif cmd[0].lower() == 'search' and len(cmd) > 1:
                    search_term = ' '.join(cmd[1:])
                    results = search_divisions(df, name_filter=search_term)
                    if results.empty:
                        print(f"No divisions found matching: {search_term}")
                    else:
                        print(f"\\nDivisions matching '{search_term}' (showing first 20):")
                        for _, row in results.head(20).iterrows():
                            print(f"  {row['Country_Name']}: {row['Administrative_Name']} "
                                  f"({row['Administrative_Level']}) - "
                                  f"({row['latitude']:.4f}, {row['longitude']:.4f})")
                
                elif cmd[0].lower() == 'stats':
                    print(f"\\nDataset Statistics:")
                    print(f"  Total divisions: {len(df):,}")
                    print(f"  Countries: {df['Country_Code'].nunique()}")
                    print(f"  Administrative levels: {df['Administrative_Level'].nunique()}")
                    print(f"\\nBy level:")
                    for level, count in df['Administrative_Level'].value_counts().sort_index().items():
                        print(f"    {level}: {count:,}")
                
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    else:
        # Command line mode
        country_code = sys.argv[1] if len(sys.argv) > 1 else None
        admin_level = sys.argv[2] if len(sys.argv) > 2 else None
        
        results = search_divisions(df, country_code, admin_level)
        
        if results.empty:
            print("No matching divisions found")
        else:
            print(f"Found {len(results)} divisions:")
            for _, row in results.iterrows():
                print(f"{row['Country_Name']}: {row['Administrative_Name']} "
                      f"({row['Administrative_Level']}) - "
                      f"Lat: {row['latitude']:.6f}, Lon: {row['longitude']:.6f}")

if __name__ == "__main__":
    main()
'''
    
    with open('coordinate_lookup.py', 'w') as f:
        f.write(lookup_script)
    
    print("✅ Created coordinate_lookup.py - Interactive coordinate lookup tool")
    
    # Create documentation about data quality
    quality_doc = '''# Data Quality and Filtering Information

## Filtering Process Applied

### 1. Administrative Level Filtering
- Only records with designation codes starting with: ADM1, ADM2, ADM3, ADM4, ADMD
- These represent official administrative divisions

### 2. Display Quality Filter
- Only records marked with display='Y' are included
- This excludes internal/technical records not meant for public display

### 3. Coordinate Quality Filter
- Only records with valid latitude and longitude coordinates
- Removes administrative divisions without geographic positioning

### 4. Deduplication Process
The dataset contains multiple name variants for the same geographic feature.
Deduplication prioritizes records based on:

**Priority Order:**
1. **Name Type (nt field):**
   - 'N' = Approved/Official names (highest priority)
   - 'C' = Conventional names (high priority)
   - 'D' = Non-authoritative names (medium priority)
   - 'V' = Variant names (lowest priority)

2. **Name Rank (name_rank field):**
   - Lower numbers = higher priority
   - Represents official preference ranking

3. **Language Priority (lang_cd field):**
   - 'eng' = English names (highest priority)
   - Local/national languages (medium priority)
   - Other languages (lowest priority)

### 5. Result
- Each unique administrative division (identified by UFI) appears only once
- The most official, preferred name is selected for each division
- All records include valid coordinates

## Column Meanings

- **Administrative_Level**: ADM1=States/Provinces, ADM2=Counties/Districts, etc.
- **Name_Type**: Type of name (N=Conventional, V=Variant)
- **Name_Rank**: Official preference ranking (lower = more preferred)
- **Language_Code**: Language of the administrative name
- **Unique_Feature_ID**: Unique identifier for the geographic feature
- **Unique_Name_ID**: Unique identifier for this specific name variant
'''
    
    with open('DATA_QUALITY_INFO.md', 'w') as f:
        f.write(quality_doc)

if __name__ == "__main__":
    print("🌍 GNS Administrative Data Processor with Coordinates")
    print("=" * 55)
    print("This script will process the complete GNS dataset to extract:")
    print("• All administrative levels (ADM1, ADM2, ADM3, ADM4)")  
    print("• Coordinates (latitude, longitude) for each division")
    print("• Country information and hierarchical relationships")
    print()
    
    # Process the main administrative data
    output_file = process_gns_administrative_data()
    
    if output_file:
        print(f"\n🎉 Processing complete!")
        print(f"📁 Main output: {output_file}")
        
        # Create the lookup tool
        create_coordinate_lookup_tool()
        print(f"🔍 Lookup tool: coordinate_lookup.py")
        
        print(f"\n📖 USAGE EXAMPLES:")
        print(f"   python3 coordinate_lookup.py CAN ADM1    # Canadian provinces")
        print(f"   python3 coordinate_lookup.py USA ADM2    # US counties") 
        print(f"   python3 coordinate_lookup.py             # Interactive mode")
        
    else:
        print("❌ Processing failed")
        sys.exit(1)
