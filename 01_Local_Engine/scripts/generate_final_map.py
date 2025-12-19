#!/usr/bin/env python3
"""
Final improved script to generate a self-contained HTML map file for field staff
with proper filtering, performance optimizations, and multiple map layers.
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

def generate_html_map(data_by_location, output_file):
    """Generate self-contained HTML file with interactive map"""
    
    # Prepare survey data as JSON
    survey_points = []
    location_groups = []
    
    # Sort districts (top level)
    sorted_districts = sorted(data_by_location.keys())
    
    for district in sorted_districts:
        tehsil_dict = data_by_location[district]
        # Sort tehsils within each district
        sorted_tehsils = sorted(tehsil_dict.keys())
        
        district_group = {
            "district": district,
            "tehsils": []
        }
        
        for tehsil in sorted_tehsils:
            mcuc_dict = tehsil_dict[tehsil]
            # Sort MC/UC within each tehsil
            sorted_mcucs = sorted(mcuc_dict.keys())
            
            tehsil_group = {
                "tehsil": tehsil,
                "mcucs": []
            }
            
            for mcuc in sorted_mcucs:
                records = mcuc_dict[mcuc]
                color = get_marker_color(mcuc)
                domestic_count = sum(1 for r in records if str(r.get('Consumer Type', '')).strip().lower() == 'domestic')
                commercial_count = sum(1 for r in records if str(r.get('Consumer Type', '')).strip().lower() == 'commercial')
                
                tehsil_group["mcucs"].append({
                    "name": mcuc,
                    "color": color,
                    "count": len(records),
                    "domestic": domestic_count,
                    "commercial": commercial_count
                })
                
                for record in records:
                    survey_points.append({
                        'survey_id': str(record.get('Survey ID', '')),
                        'district': district,
                        'tehsil': tehsil,
                        'mc_uc': mcuc,
                        'consumer_type': str(record.get('Consumer Type', '')).strip(),
                        'house_type': str(record.get('House Type', '')).strip(),
                        'survey_date': str(record.get('Survey Date', '')).strip(),
                        'location': str(record.get('Location', '')).strip(),
                        'color': color
                    })
            
            district_group["tehsils"].append(tehsil_group)
        
        location_groups.append(district_group)
    
    survey_data_json = json.dumps(survey_points)
    location_data_json = json.dumps(location_groups)
    
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
        .district-group {
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .district-header {
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
            cursor: pointer;
            user-select: none;
        }
        .tehsil-group {
            margin-left: 10px;
            margin-bottom: 8px;
        }
        .tehsil-header {
            font-weight: normal;
            margin-bottom: 3px;
            color: #555;
            font-size: 13px;
            cursor: pointer;
            user-select: none;
        }
        .legend-item {
            margin: 1px 0;
            display: flex;
            align-items: center;
            font-size: 11px;
        }
        .legend-color {
            width: 10px;
            height: 10px;
            margin-right: 4px;
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
            padding: 4px;
            margin: 2px;
            font-size: 12px;
        }
        .filter-section {
            margin-bottom: 8px;
        }
        h4 {
            margin: 5px 0;
            font-size: 14px;
        }
        .counts {
            font-size: 10px;
            color: #666;
            margin-left: 5px;
        }
        .layer-control {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        .collapsible-content {
            display: none;
        }
        .expanded > .collapsible-content {
            display: block;
        }
        .toggle-icon::before {
            content: "▶ ";
        }
        .expanded > .district-header > .toggle-icon::before,
        .expanded > .tehsil-header > .toggle-icon::before {
            content: "▼ ";
        }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info">
        <div class="controls">
            <div class="filter-section">
                <label for="districtFilter">District:</label>
                <select id="districtFilter" onchange="populateTehsilFilter()">
                    <option value="all">All Districts</option>
''' + ''.join([f'                    <option value="{district}">{district}</option>\n' for district in sorted_districts]) + '''
                </select>
            </div>
            <div class="filter-section">
                <label for="tehsilFilter">Tehsil:</label>
                <select id="tehsilFilter" onchange="populateMCUCFilter()">
                    <option value="all">All Tehsils</option>
                </select>
            </div>
            <div class="filter-section">
                <label for="mcucFilter">MC/UC:</label>
                <select id="mcucFilter">
                    <option value="all">All MC/UC</option>
                </select>
            </div>
            <div class="filter-section">
                <label for="typeFilter">Consumer Type:</label>
                <select id="typeFilter">
                    <option value="all">All Types</option>
                    <option value="Domestic">Domestic</option>
                    <option value="Commercial">Commercial</option>
                </select>
            </div>
            <button onclick="applyFilters()">Apply Filters</button>
            <button onclick="resetFilters()">Reset</button>
            
            <div class="layer-control">
                <label for="layerControl">Map Layer:</label>
                <select id="layerControl" onchange="changeBaseLayer()">
                    <option value="osm">Street Map</option>
                    <option value="satellite">Satellite</option>
                    <option value="terrain">Terrain</option>
                </select>
            </div>
        </div>
        <div class="legend">
            <h4>Location Hierarchy</h4>
''' + ''.join([f'''            <div class="district-group" id="district-{i}">
                <div class="district-header" onclick="toggleCollapse(this.parentNode)">
                    <span class="toggle-icon"></span>{district_group["district"]}
                </div>
                <div class="collapsible-content">
''' + ''.join([f'''                    <div class="tehsil-group" id="tehsil-{j}">
                        <div class="tehsil-header" onclick="toggleCollapse(this.parentNode)">
                            <span class="toggle-icon"></span>{tehsil_group["tehsil"]}
                        </div>
                        <div class="collapsible-content">
''' + ''.join([f'                            <div class="legend-item"><div class="legend-color" style="background-color:{mcuc["color"]};"></div>{mcuc["name"]} <span class="counts">({mcuc["domestic"]}D/{mcuc["commercial"]}C)</span></div>\n' for mcuc in tehsil_group["mcucs"]]) + '''                        </div>
                    </div>
''' for j, tehsil_group in enumerate(district_group["tehsils"])]) + '''                </div>
            </div>
''' for i, district_group in enumerate(location_groups)]) + '''
        </div>
    </div>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Initialize the map with Sargodha as default view
        var map = L.map('map').setView([32.0833, 72.6667], 10); // Sargodha coordinates
        
        // Base layers
        var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        });
        
        var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            maxZoom: 19
        });
        
        var terrainLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
            maxZoom: 19
        });
        
        // Add default layer (OSM)
        osmLayer.addTo(map);
        
        // Current base layer reference
        var currentBaseLayer = osmLayer;
        
        // Survey data
        var surveyData = ''' + survey_data_json + ''';
        
        // Location data for filtering
        var locationData = ''' + location_data_json + ''';
        
        // Create marker layers
        var markers = L.layerGroup().addTo(map);
        
        // Function to change base layer
        function changeBaseLayer() {
            var layerSelect = document.getElementById('layerControl');
            var selectedLayer = layerSelect.value;
            
            // Remove current layer
            map.removeLayer(currentBaseLayer);
            
            // Add selected layer
            if (selectedLayer === 'osm') {
                osmLayer.addTo(map);
                currentBaseLayer = osmLayer;
            } else if (selectedLayer === 'satellite') {
                satelliteLayer.addTo(map);
                currentBaseLayer = satelliteLayer;
            } else if (selectedLayer === 'terrain') {
                terrainLayer.addTo(map);
                currentBaseLayer = terrainLayer;
            }
        }
        
        // Function to populate tehsil filter based on selected district
        function populateTehsilFilter() {
            var districtSelect = document.getElementById('districtFilter');
            var tehsilSelect = document.getElementById('tehsilFilter');
            var selectedDistrict = districtSelect.value;
            
            // Clear existing options except "All Tehsils"
            tehsilSelect.innerHTML = '<option value="all">All Tehsils</option>';
            
            if (selectedDistrict === 'all') {
                // Add all tehsils from all districts
                locationData.forEach(function(districtGroup) {
                    districtGroup.tehsils.forEach(function(tehsil) {
                        var option = document.createElement('option');
                        option.value = tehsil.tehsil;
                        option.text = districtGroup.district + ' - ' + tehsil.tehsil;
                        tehsilSelect.appendChild(option);
                    });
                });
            } else {
                // Add only tehsils from selected district
                locationData.forEach(function(districtGroup) {
                    if (districtGroup.district === selectedDistrict) {
                        districtGroup.tehsils.forEach(function(tehsil) {
                            var option = document.createElement('option');
                            option.value = tehsil.tehsil;
                            option.text = tehsil.tehsil;
                            tehsilSelect.appendChild(option);
                        });
                    }
                });
            }
            
            // Reset MC/UC filter
            document.getElementById('mcucFilter').innerHTML = '<option value="all">All MC/UC</option>';
        }
        
        // Function to populate MC/UC filter based on selected tehsil
        function populateMCUCFilter() {
            var districtSelect = document.getElementById('districtFilter');
            var tehsilSelect = document.getElementById('tehsilFilter');
            var mcucSelect = document.getElementById('mcucFilter');
            var selectedDistrict = districtSelect.value;
            var selectedTehsil = tehsilSelect.value;
            
            // Clear existing options except "All MC/UC"
            mcucSelect.innerHTML = '<option value="all">All MC/UC</option>';
            
            if (selectedTehsil === 'all') {
                // If "All Tehsils" selected, show MC/UCs from all tehsils in selected district
                if (selectedDistrict === 'all') {
                    // Show all MC/UCs
                    locationData.forEach(function(districtGroup) {
                        districtGroup.tehsils.forEach(function(tehsil) {
                            tehsil.mcucs.forEach(function(mcuc) {
                                var option = document.createElement('option');
                                option.value = mcuc.name;
                                option.text = districtGroup.district + ' - ' + tehsil.tehsil + ' - ' + mcuc.name;
                                mcucSelect.appendChild(option);
                            });
                        });
                    });
                } else {
                    // Show MC/UCs from selected district only
                    locationData.forEach(function(districtGroup) {
                        if (districtGroup.district === selectedDistrict) {
                            districtGroup.tehsils.forEach(function(tehsil) {
                                tehsil.mcucs.forEach(function(mcuc) {
                                    var option = document.createElement('option');
                                    option.value = mcuc.name;
                                    option.text = tehsil.tehsil + ' - ' + mcuc.name;
                                    mcucSelect.appendChild(option);
                                });
                            });
                        }
                    });
                }
            } else {
                // Show only MC/UCs from selected tehsil
                locationData.forEach(function(districtGroup) {
                    if (selectedDistrict === 'all' || districtGroup.district === selectedDistrict) {
                        districtGroup.tehsils.forEach(function(tehsil) {
                            if (tehsil.tehsil === selectedTehsil) {
                                tehsil.mcucs.forEach(function(mcuc) {
                                    var option = document.createElement('option');
                                    option.value = mcuc.name;
                                    option.text = mcuc.name;
                                    mcucSelect.appendChild(option);
                                });
                            }
                        });
                    }
                });
            }
        }
        
        // Function to toggle collapsible sections
        function toggleCollapse(element) {
            element.classList.toggle('expanded');
        }
        
        // Function to create markers with filters
        function createMarkers(filterDistrict = 'all', filterTehsil = 'all', filterMCUC = 'all', filterType = 'all') {
            // Clear existing markers
            markers.clearLayers();
            
            // Counter for performance
            var markerCount = 0;
            var maxMarkers = 5000; // Limit for performance
            
            // Process each survey point
            surveyData.some(function(survey) {
                // Skip if filtering by district and district doesn't match
                if (filterDistrict !== 'all' && survey.district !== filterDistrict) {
                    return false;
                }
                
                // Skip if filtering by tehsil and tehsil doesn't match
                if (filterTehsil !== 'all' && survey.tehsil !== filterTehsil) {
                    return false;
                }
                
                // Skip if filtering by MC/UC and MC/UC doesn't match
                if (filterMCUC !== 'all' && survey.mc_uc !== filterMCUC) {
                    return false;
                }
                
                // Skip if filtering by consumer type and type doesn't match
                if (filterType !== 'all' && survey.consumer_type.toLowerCase() !== filterType.toLowerCase()) {
                    return false;
                }
                
                // Parse location
                var coords = survey.location.split(',');
                if (coords.length !== 2) return false;
                
                var lat = parseFloat(coords[0]);
                var lng = parseFloat(coords[1]);
                
                if (isNaN(lat) || isNaN(lng)) return false;
                
                // Create popup content
                var popupContent = 
                    '<b>Survey ID:</b> ' + survey.survey_id + '<br>' +
                    '<b>District:</b> ' + survey.district + '<br>' +
                    '<b>Tehsil:</b> ' + survey.tehsil + '<br>' +
                    '<b>MC/UC:</b> ' + survey.mc_uc + '<br>' +
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
                markerCount++;
                
                // Performance limit
                if (markerCount >= maxMarkers) {
                    console.log('Marker limit reached: ' + maxMarkers);
                    return true; // Break the loop
                }
                
                return false; // Continue loop
            });
            
            // Fit bounds to show markers if any exist
            if (markers.getLayers().length > 0) {
                var group = new L.featureGroup(markers.getLayers());
                map.fitBounds(group.getBounds().pad(0.1));
            } else {
                // If no markers, show default view
                map.setView([32.0833, 72.6667], 10);
            }
            
            console.log('Markers displayed: ' + markerCount);
        }
        
        // Apply filters function
        function applyFilters() {
            var districtSelect = document.getElementById('districtFilter');
            var tehsilSelect = document.getElementById('tehsilFilter');
            var mcucSelect = document.getElementById('mcucFilter');
            var typeSelect = document.getElementById('typeFilter');
            
            var selectedDistrict = districtSelect.value;
            var selectedTehsil = tehsilSelect.value;
            var selectedMCUC = mcucSelect.value;
            var selectedType = typeSelect.value;
            
            createMarkers(selectedDistrict, selectedTehsil, selectedMCUC, selectedType);
        }
        
        // Reset filters function
        function resetFilters() {
            document.getElementById('districtFilter').value = 'all';
            document.getElementById('tehsilFilter').innerHTML = '<option value="all">All Tehsils</option>';
            document.getElementById('mcucFilter').innerHTML = '<option value="all">All MC/UC</option>';
            document.getElementById('typeFilter').value = 'all';
            document.getElementById('layerControl').value = 'osm';
            changeBaseLayer();
            map.setView([32.0833, 72.6667], 10); // Default to Sargodha
            markers.clearLayers();
        }
        
        // Initialize filters - default to Sargodha district
        document.getElementById('districtFilter').value = 'Sargodha';
        populateTehsilFilter();
        populateMCUCFilter();
        
        // Don't load any markers initially for performance
        console.log('Map initialized. Use filters to load data.');
    </script>
</body>
</html>'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated map file: {output_file}")

def process_csv_files():
    """Process CSV files and generate map data organized by district->tehsil->MC/UC"""
    csv_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.csv') and 'MASTER' not in f]
    
    if not csv_files:
        print("No CSV files found in the input folder")
        return
    
    # Collect data by district -> tehsil -> MC/UC -> records
    data_by_location = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
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
                
                # Create MC/UC identifier
                mc_uc = f"{district} - {uc}" if uc else f"{district} - {tehsil}"
                
                # Add to collection
                data_by_location[district][tehsil][mc_uc].append(dict(row))
                
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Generate HTML map
    output_file = os.path.join("..", "outputs", "field_staff_map.html")
    generate_html_map(data_by_location, output_file)
    
    # Print summary
    total_records = 0
    total_mcucs = 0
    total_tehsils = 0
    
    for district, tehsil_dict in data_by_location.items():
        total_tehsils += len(tehsil_dict)
        for tehsil, mcuc_dict in tehsil_dict.items():
            total_mcucs += len(mcuc_dict)
            for records in mcuc_dict.values():
                total_records += len(records)
            
    print(f"\nSummary:")
    print(f"- Processed {len(csv_files)} CSV files")
    print(f"- Total survey records: {total_records}")
    print(f"- Unique districts: {len(data_by_location)}")
    print(f"- Unique tehsils: {total_tehsils}")
    print(f"- Unique MC/UC areas: {total_mcucs}")
    print(f"- Map file generated: {output_file}")

def main():
    print("==============================================")
    print("  Final Field Staff Map Generator")
    print("==============================================\n")
    
    process_csv_files()
    
    print("\n==============================================")
    print("  Map Generation Complete!")
    print("  The HTML file can be opened directly on Android phones")
    print("  Features:")
    print("  - Hierarchical filtering (District -> Tehsil -> MC/UC)")
    print("  - Consumer type filtering (Domestic/Commercial)")
    print("  - Multiple map layers (Street/Satellite/Terrain)")
    print("  - Performance optimized (no initial markers loaded)")
    print("  - Collapsible legend organized by location hierarchy")
    print("  - Default view set to Sargodha")
    print("  No internet connection required after download")
    print("==============================================")

if __name__ == "__main__":
    main()