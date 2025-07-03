# Country and Administrative Division Data Processor

## Project Overview

This project provides a comprehensive, cleaned, and ready-to-use dataset of global administrative divisions. It processes raw data from the GEOnet Names Server (GNS), which often contains multiple name variants, languages, and historical names for a single geographic feature.

The included Python scripts automate the entire workflow: from reading the raw data, applying intelligent filtering to select the best and most relevant names, integrating coordinate data, and finally exporting the results into user-friendly Excel files.

## Final Data Products

The process generates two main outputs:

1.  **`Complete_Administrative_Divisions_with_Coordinates.xlsx`**: A single, comprehensive Excel file containing all administrative divisions (levels 1-4) for all countries. This is the master dataset.
2.  **`Country_Exports/`**: A directory containing individual Excel files for each of the 217 countries, split from the main data file for easier, country-specific analysis.

## Data Dictionary

The final Excel files contain the following key columns:

*   **`Country_Name`**: The common English name of the country.
*   **`Admin_Level`**: The administrative level of the division (e.g., ADM1, ADM2).
*   **`Subdivision_Name`**: The cleaned, official, or most common name for the administrative division.
*   **`Latitude`**: The geographic latitude in decimal degrees.
*   **`Longitude`**: The geographic longitude in decimal degrees.
*   **`UFI`**: Unique Feature Identifier, a stable ID for a single geographic feature.
*   **`UNI`**: Unique Name Identifier, an ID for a specific name variant of a feature.
*   **`Name_Type`**: The code indicating the type of name (e.g., 'N' for Official, 'C' for Conventional).

## The Application (Scripts)

This workspace contains the following Python scripts:

*   **`process_all_administrative_levels.py`**: The core script of this project. It reads the raw, complex GNS data files, applies sophisticated filtering to deduplicate and select the highest-quality names, and generates the final `Complete_Administrative_Divisions_with_Coordinates.xlsx` file.
*   **`split_by_country.py`**: A utility script that takes the main Excel file and splits it into separate files for each country, populating the `Country_Exports/` directory.
*   **`query_subdivisions.py`**: An early, interactive script for querying the initial `ADM1_Codes.csv` data. Kept for reference.
*   **`process_subdivisions.py`**: The first script created to process only the ADM1 level data. Also kept for reference.

## Data Processing Logic

To ensure the highest data quality, the processing script implements the following logic:

*   **Name Prioritization**: It filters names based on the `Name_Type` (`nt`) field, prioritizing official (`N`) and conventional (`C`) names over variants (`V`).
*   **Rank-Based Selection**: It uses the `name_rank` to select the most prominent name when multiple valid options exist for a single feature.
*   **Hierarchical Structuring**: It correctly identifies and labels the administrative level (ADM1, ADM2, etc.) for each division.

## Data Source

The raw data for this project is sourced from the [GEOnet Names Server (GNS)](https://geonames.nga.mil/geonames/GNSData/). The specific files used are:

*   **Administrative Regions**: [https://geonames.nga.mil/geonames/GNSData/fc_files/Administrative_Regions.zip](https://geonames.nga.mil/geonames/GNSData/fc_files/Administrative_Regions.zip)
*   **Areas & Localities**: [https://geonames.nga.mil/geonames/GNSData/fc_files/Areas_Localities.zip](https://geonames.nga.mil/geonames/GNSData/fc_files/Areas_Localities.zip)

## How to Re-run the Process

If you need to regenerate the data from the raw source files (assuming they are present), follow these steps:

1.  **Run the main processing script:**
    ```bash
    python3 process_all_administrative_levels.py
    ```
2.  **Run the splitting script:**
    ```bash
    python3 split_by_country.py
    ```