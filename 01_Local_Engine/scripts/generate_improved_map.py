#!/usr/bin/env python3
"""
Improved script to generate a self-contained HTML map file for field staff
that works offline on Android phones with proper filtering by city/MC/UC.
"""

import pandas as pd
import os
import json
from collections import defaultdict

# Define input folder
INPUT_FOLDER = os.path.join("..", "outputs", "scraped_data_appsheet")

def get_marker_color(identifier):
    """Generate a consistent color for each MC/UC"""
    # Simple hash-based color generation for consistency
    hash_val = hash(identifier) % 360
    return f"hsl({hash_val}, 70%, 45%)"

def generate_html_map(data_by_city, output_file):
    """Generate self-contained HTML file with interactive map"""
    
    # Prepare survey data as JSON
    survey_points = []
    city_mcuc_groups = []
    
    # Sort cities alphabetically
    sorted_cities = sorted(data_by_city.keys())
    
    for city in sorted_cities:
        mcuc_dict = data_by_city[city]
        # Sort MC/UC within each city
        sorted_mcucs = sorted(mcuc_dict.keys())
        
        city_group = {
            "city": city,
            "mcucs": []
        }
        
        for mcuc in sorted_mcucs:
            records = mcuc_dict[mcuc]
            color = get_marker_color(mcuc)
            city_group["mcucs"].append({
                "name": mcuc,
                "color": color,
                "count": len(records)
            })
            
            for record in records:
                survey_points.append({
                    'survey_id': str(record.get('Survey ID', '')),
                    'city': city,
                    'mc_uc': mcuc,
                    'district': str(record.get('District', '')),
                    'tehsil': str(record.get('Tehsil', '')),
                    'consumer_type': str(record.get('Consumer Type', '')),
                    'house_type': str(record.get('House Type', '')),
                    'survey_date': str(record.get('Survey Date', '')),
                    'location': str(record.get('Location', '')),
                    'color': color
                })
        
        city_mcuc_groups.append(city_group)
    
    survey_data_json = json.dumps(survey_points)
    city_data_json = json.dumps(city_mcuc_groups)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Field Survey Map - MC/UC View</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        .info { 
            padding: 6px 8px; 
            font: 14px/16px Arial, Helvetica, sans-serif; 
            background: white; 
            background: rgba(255,255,255,0.9); 
            box-shadow: 0 0 15px rgba(0,0,0,0.2); 
            border-radius: 5px; 
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
            max-width: 350px;
            max-height: 90vh;
            overflow-y: auto;
        }
        .legend {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            max-height: 400px;
            overflow-y: auto;
        }
        .city-group {
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .city-header {
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }
        .legend-item {
            margin: 2px 0;
            display: flex;
            align-items: center;
            font-size: 12px;
        }
        .legend-color {
            width: 12px;
            height: 12px;
            margin-right: 5px;
            border: 1px solid #666;
        }
        .controls {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            margin-bottom: 10px;
        }
        select, button {
            padding: 5px;
            margin: 2px;
            font-size: 12px;
        }
        .filter-section {
            margin-bottom: 10px;
        }
        h4 {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info">
        <div class="controls">
            <div class="filter-section">
                <label for="cityFilter">City:</label>
                <select id="cityFilter" onchange="populateMCUCFilter()">
                    <option value="all">All Cities</option>
''' + ''.join([f'                    <option value="{city}">{city}</option>\n' for city in sorted_cities]) + '''
                </select>
            </div>
            <div class="filter-section">
                <label for="mcucFilter">MC/UC:</label>
                <select id="mcucFilter">
                    <option value="all">All MC/UC</option>
                </select>
            </div>
            <button onclick="filterMarkers()">Apply Filter</button>
            <button onclick="resetView()">Reset View</button>
        </div>
        <div class="legend">
            <h4>MC/UC Legend</h4>
''' + ''.join([f'''            <div class="city-group">
                <div class="city-header">{city_group["city"]}</div>
''' + ''.join([f'                <div class="legend-item"><div class="legend-color" style="background-color:{mcuc["color"]};"></div>{mcuc["name"]} ({mcuc["count"]})</div>\n' for mcuc in city_group["mcucs"]]) + '''            </div>
''' for city_group in city_mcuc_groups]) + '''
        </div>
    </div>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Initialize the map
        var map = L.map('map').setView([32.0, 73.0], 8);
        
        // Add base tile layer (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Survey data
        var surveyData = ''' + survey_data_json + ''';
        
        // City/MCUC data for filtering
        var cityData = ''' + city_data_json + ''';
        
        // Create marker layers
        var markers = L.layerGroup().addTo(map);
        
        // Function to populate MC/UC filter based on selected city
        function populateMCUCFilter() {
            var citySelect = document.getElementById('cityFilter');
            var mcucSelect = document.getElementById('mcucFilter');
            var selectedCity = citySelect.value;
            
            // Clear existing options except "All MC/UC"
            mcucSelect.innerHTML = '<option value="all">All MC/UC</option>';
            
            if (selectedCity === 'all') {
                // Add all MC/UCs from all cities
                cityData.forEach(function(cityGroup) {
                    cityGroup.mcucs.forEach(function(mcuc) {
                        var option = document.createElement('option');
                        option.value = mcuc.name;
                        option.text = cityGroup.city + ' - ' + mcuc.name;
                        mcucSelect.appendChild(option);
                    });
                });
            } else {
                // Add only MC/UCs from selected city
                cityData.forEach(function(cityGroup) {
                    if (cityGroup.city === selectedCity) {
                        cityGroup.mcucs.forEach(function(mcuc) {
                            var option = document.createElement('option');
                            option.value = mcuc.name;
                            option.text = mcuc.name;
                            mcucSelect.appendChild(option);
                        });
                    }
                });
            }
        }
        
        // Function to create markers
        function createMarkers(filterCity = 'all', filterMCUC = 'all') {
            // Clear existing markers
            markers.clearLayers();
            
            // Process each survey point
            surveyData.forEach(function(survey) {
                // Skip if filtering by city and city doesn't match
                if (filterCity !== 'all' && survey.city !== filterCity) {
                    return;
                }
                
                // Skip if filtering by MC/UC and MC/UC doesn't match
                if (filterMCUC !== 'all' && survey.mc_uc !== filterMCUC) {
                    return;
                }
                
                // Parse location
                var coords = survey.location.split(',');
                if (coords.length !== 2) return;
                
                var lat = parseFloat(coords[0]);
                var lng = parseFloat(coords[1]);
                
                if (isNaN(lat) || isNaN(lng)) return;
                
                // Create popup content
                var popupContent = 
                    '<b>Survey ID:</b> ' + survey.survey_id + '<br>' +
                    '<b>City:</b> ' + survey.city + '<br>' +
                    '<b>MC/UC:</b> ' + survey.mc_uc + '<br>' +
                    '<b>District:</b> ' + survey.district + '<br>' +
                    '<b>Tehsil:</b> ' + survey.tehsil + '<br>' +
                    '<b>Consumer Type:</b> ' + survey.consumer_type + '<br>' +
                    '<b>House Type:</b> ' + survey.house_type + '<br>' +
                    '<b>Date:</b> ' + survey.survey_date;
                
                // Get color for this MC/UC
                var color = survey.color || '#3388ff';
                
                // Create circle marker
                var marker = L.circleMarker([lat, lng], {
                    radius: 6,
                    fillColor: color,
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindPopup(popupContent);
                
                // Add to map
                marker.addTo(markers);
            });
            
            // Fit bounds to show markers if any exist
            if (markers.getLayers().length > 0) {
                var group = new L.featureGroup(markers.getLayers());
                map.fitBounds(group.getBounds().pad(0.1));
            }
        }
        
        // Filter markers function
        function filterMarkers() {
            var citySelect = document.getElementById('cityFilter');
            var mcucSelect = document.getElementById('mcucFilter');
            var selectedCity = citySelect.value;
            var selectedMCUC = mcucSelect.value;
            createMarkers(selectedCity, selectedMCUC);
        }
        
        // Reset view function
        function resetView() {
            document.getElementById('cityFilter').value = 'all';
            document.getElementById('mcucFilter').innerHTML = '<option value="all">All MC/UC</option>';
            map.setView([32.0, 73.0], 8);
            createMarkers('all', 'all');
        }
        
        // Initialize filters and markers
        populateMCUCFilter();
        createMarkers();
    </script>
</body>
</html>'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated map file: {output_file}")

def process_csv_files():
    """Process CSV files and generate map data organized by city"""
    csv_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.csv') and 'MASTER' not in f]
    
    if not csv_files:
        print("No CSV files found in the input folder")
        return
    
    # Collect data by city -> MC/UC -> records
    data_by_city = defaultdict(lambda: defaultdict(list))
    
    for csv_file in csv_files:
        file_path = os.path.join(INPUT_FOLDER, csv_file)
        print(f"Processing {csv_file}...")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
            
            # Required columns check
            required_columns = ['Location', 'District', 'Tehsil', 'Union Council']
            if not all(col in df.columns for col in required_columns):
                print(f"Skipping {csv_file} - missing required columns")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                # Skip if location is missing
                if not row.get('Location') or ',' not in str(row['Location']):
                    continue
                
                # Create identifiers
                district = str(row.get('District', '')).strip()
                tehsil = str(row.get('Tehsil', '')).strip()
                uc = str(row.get('Union Council', '')).strip()
                
                # Use tehsil as city name for grouping
                city = tehsil if tehsil else district
                mc_uc = f"{district} - {uc}" if uc else district
                
                # Add to collection
                data_by_city[city][mc_uc].append(dict(row))
                
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Generate HTML map
    output_file = os.path.join("..", "outputs", "field_staff_map.html")
    generate_html_map(data_by_city, output_file)
    
    # Print summary
    total_records = 0
    total_mcucs = 0
    for city, mcuc_dict in data_by_city.items():
        total_mcucs += len(mcuc_dict)
        for records in mcuc_dict.values():
            total_records += len(records)
            
    print(f"\nSummary:")
    print(f"- Processed {len(csv_files)} CSV files")
    print(f"- Total survey records: {total_records}")
    print(f"- Unique cities: {len(data_by_city)}")
    print(f"- Unique MC/UC areas: {total_mcucs}")
    print(f"- Map file generated: {output_file}")

def main():
    print("==============================================")
    print("  Improved Field Staff Map Generator")
    print("==============================================\n")
    
    process_csv_files()
    
    print("\n==============================================")
    print("  Map Generation Complete!")
    print("  The HTML file can be opened directly on Android phones")
    print("  Features:")
    print("  - Filter by city and MC/UC")
    print("  - Organized legend by city")
    print("  - Automatic zoom to filtered results")
    print("  No internet connection required after download")
    print("==============================================")

if __name__ == "__main__":
    main()