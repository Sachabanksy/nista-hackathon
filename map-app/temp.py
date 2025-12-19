import json

def find_keys_in_json(data, target_keys, path="", results=None):
    """
    Recursively search for target keys in nested JSON structure
    
    Args:
        data: JSON data (dict, list, or other)
        target_keys: List of keys to search for
        path: Current path in the JSON (for tracking location)
        results: Dictionary to store found keys and their paths
    
    Returns:
        Dictionary with keys as found target_keys and values as lists of paths where found
    """
    if results is None:
        results = {key: [] for key in target_keys}
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if this key is one we're looking for
            if key in target_keys:
                results[key].append({
                    'path': current_path,
                    'value': value
                })
            
            # Recurse into the value
            find_keys_in_json(value, target_keys, current_path, results)
    
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = f"{path}[{idx}]"
            find_keys_in_json(item, target_keys, current_path, results)
    
    return results

def explore_geojson_structure(geojson_path):
    """Load geojson and find RGN24CD and RGN24NM"""
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    target_keys = ['RGN24CD', 'RGN24NM']
    results = find_keys_in_json(geojson_data, target_keys)
    
    print("Search Results:")
    print("=" * 60)
    for key, findings in results.items():
        print(f"\n{key}: Found {len(findings)} occurrences")
        if findings:
            print(f"  First occurrence at: {findings[0]['path']}")
            print(f"  Sample value: {findings[0]['value']}")
            if len(findings) > 1:
                print(f"  ... and {len(findings) - 1} more")
    
    return results

def load_regions_from_geojson(geojson_path):
    """Extract region codes using RGN24CD and RGN24NM"""
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    regions = {}
    for feature in geojson_data['features']:
        props = feature['properties']
        region_code = props.get('RGN24CD')
        region_name = props.get('RGN24NM')
        
        if region_code:
            regions[region_code] = region_name
    
    return regions

def main():
    geojson_path = 'data/Regions_December_2024_Boundaries_EN_BFC_1195854647342073399.geojson'
    
    # First, explore the structure
    print("Exploring geojson structure...\n")
    results = explore_geojson_structure(geojson_path)
    
    # Then load the regions
    print("\n" + "=" * 60)
    print("\nLoading regions...")
    regions = load_regions_from_geojson(geojson_path)
    print(f"Found {len(regions)} regions")
    print("\nSample regions:")
    for code, name in list(regions.items())[:5]:
        print(f"  {code}: {name}")

if __name__ == "__main__":
    main()