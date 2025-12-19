import pandas as pd
import numpy as np
import random
import json
from datetime import datetime, timedelta

def load_regions_from_geojson(geojson_path):
    """Extract region codes from the geojson file using RGN24CD and RGN24NM"""
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    regions = {}
    for feature in geojson_data['features']:
        # Use RGN24CD for region code and RGN24NM for region name
        region_code = feature['properties'].get('RGN24CD')
        region_name = feature['properties'].get('RGN24NM')
        
        if region_code:
            regions[region_code] = region_name
    
    return regions

def seed_fake_data_from_geojson(geojson_path, entries_per_region=10):
    """Generate fake data for all regions in the geojson"""
    
    # Load actual regions from geojson
    regions = load_regions_from_geojson(geojson_path)
    print(f"Loaded {len(regions)} regions from geojson")
    
    # Topics
    topic_names = [
        'Climate Change', 'Technology', 'Health', 'Education', 'Economy',
        'Housing', 'Brexit', 'NHS', 'Cost of Living', 'Energy Prices',
        'Immigration', 'Transport', 'Tourism', 'Football', 'Royal Family'
    ]
    
    data = []
    
    # Generate data for each region
    for region_code, region_name in regions.items():
        for _ in range(entries_per_region):
            date = datetime.now() - timedelta(days=random.randint(0, 365))
            topic_name = random.choice(topic_names)
            
            # Create more realistic interest values
            base_interest = random.randint(20, 80)
            interest_value = max(0, min(100, base_interest + random.randint(-15, 15)))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'topic_name': topic_name,
                'region': region_code,
                'region_name': region_name,
                'interest_value': interest_value
            })
    
    df = pd.DataFrame(data)
    df = df.sort_values('date').reset_index(drop=True)
    return df

def main():
    geo_json_path = 'data/Regions_December_2024_Boundaries_EN_BFC_1195854647342073399.geojson'
    
    fake_data_df = seed_fake_data_from_geojson(geo_json_path, entries_per_region=15)
    
    print("Created fake data")
    print(f"Date range: {fake_data_df['date'].min()} to {fake_data_df['date'].max()}")
    print(f"Unique regions: {fake_data_df['region'].nunique()}")
    print(f"Unique topics: {fake_data_df['topic_name'].nunique()}")
    print(f"Total entries: {len(fake_data_df)}")
    print("\nSample regions:")
    print(fake_data_df[['region', 'region_name']].drop_duplicates().head(10))
    
    fake_data_df.to_csv('data/fake_google_trends_data.csv', index=False)
    print("\nSaved fake data to data/fake_google_trends_data.csv")

if __name__ == "__main__":
    main()