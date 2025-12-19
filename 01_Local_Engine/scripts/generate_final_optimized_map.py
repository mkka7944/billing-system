#!/usr/bin/env python3
"""
Final optimized field staff map generator with improved naming and formatting.
"""

import pandas as pd
import os
import json
import re
from collections import defaultdict

# Define input folder
INPUT_FOLDER = os.path.join("..", "outputs", "scraped_data")

def get_marker_color(identifier):
    """Generate a consistent color for each MC/UC with better differentiation"""
    # Use a more spread-out hashing algorithm to ensure better color distribution
    hash_val = hash(identifier) % 360
    # Ensure colors are more distinct by using larger intervals
    hue_spread = (hash_val * 137.508) % 360  # Golden angle approximation for better distribution
    saturation = 70 + (hash_val % 30)  # Vary saturation between 70-100%
    lightness = 40 + (hash_val % 20)   # Vary lightness between 40-60%
    return f"hsl({hue_spread}, {saturation}%, {lightness}%)"

def shorten_mcuc_name(mcuc_name, district, tehsil):
    """Shorten MC/UC names with specific formatting for each district/tehsil"""
    name = mcuc_name
    import re
    
    # Special handling for Sargodha district
    if district == "Sargodha":
        # Remove district prefix
        if name.startswith(district + " - "):
            name = name[len(district + " - "):]
            
        # For Sargodha tehsil
        if tehsil == "Sargodha":
            # Extract MC-1, MC-2, etc. pattern
            mc_match = re.search(r'(MC[-\s]*\d+)', name, re.IGNORECASE)
            if mc_match:
                name = mc_match.group(1).upper()
            else:
                # Fallback: just get the first part after comma
                if ',' in name:
                    name = name.split(',')[0].strip()
                else:
                    # If no comma, just use the first few characters as identifier
                    parts = name.split()
                    if parts:
                        name = parts[0]
        # For Bhalwal tehsil
        elif tehsil == "Bhalwal":
            # Remove "Sargodha - " prefix if present
            if name.startswith("Sargodha - "):
                name = name[len("Sargodha - "):]
            # Extract UC-1, UC-2, etc. pattern
            uc_match = re.search(r'(UC[-\s]*\d+)', name, re.IGNORECASE)
            if uc_match:
                name = uc_match.group(1).upper()
            else:
                # Fallback: just get the first part after comma
                if ',' in name:
                    name = name.split(',')[0].strip()
                else:
                    # If no comma, just use the first few characters as identifier
                    parts = name.split()
                    if parts:
                        name = parts[0]
    
    # Special handling for Khushab district
    elif district == "Khushab":
        # Remove district prefix
        if name.startswith(district + " - "):
            name = name[len(district + " - "):]
        # Extract Zone/Ward information in specific format
        zone_match = re.search(r'(Zone[-\s]*\d+)', name, re.IGNORECASE)
        ward_match = re.search(r'(Ward[-\s]*\d+)', name, re.IGNORECASE)
        # Also look for location-specific identifiers
        location_match = re.search(r'([A-Za-z]+\s*[A-Za-z]*)\s*(?:/|,|Ward)', name)
        
        if zone_match and ward_match:
            zone = zone_match.group(1).replace('-', '').replace(' ', '').upper()
            ward = ward_match.group(1).replace('-', '').replace(' ', '').upper()
            # Add location identifier if available
            if location_match:
                location = location_match.group(1).strip().replace(' ', '').upper()
                name = f"{zone}/{ward}/{location}"
            else:
                name = f"{zone}/{ward}"
        elif zone_match:
            name = zone_match.group(1).replace('-', '').replace(' ', '').upper()
        elif ward_match:
            name = ward_match.group(1).replace('-', '').replace(' ', '').upper()
        elif location_match:
            name = location_match.group(1).strip().replace(' ', '').upper()
    
    # General fallback for other districts
    else:
        # Remove district and tehsil prefixes
        if name.startswith(district + " - "):
            name = name[len(district + " - "):]
        if name.startswith(tehsil + " - "):
            name = name[len(tehsil + " - "):]
        
        # Try to extract MC/UC pattern
        mc_match = re.search(r'(MC[-\s]*\d+)', name, re.IGNORECASE)
        uc_match = re.search(r'(UC[-\s]*\d+|[Uu]nion\s*[Cc]ouncil[-\s]*\d+)', name, re.IGNORECASE)
        if mc_match:
            name = mc_match.group(1).upper()
        elif uc_match:
            name = uc_match.group(1).upper()
        else:
            # Final fallback - use first part before comma or first word
            if ',' in name:
                name = name.split(',')[0].strip()
            else:
                parts = name.split()
                if parts:
                    name = parts[0]
    
    return name if name else mcuc_name

def generate_html_map(data_by_location, output_file):
    """Generate optimized HTML file with improved naming"""
    
    # Prepare survey data as JSON and calculate totals
    survey_points = []
    location_groups = []
    
    # Sort districts - put Sargodha first, then others alphabetically
    all_districts = list(data_by_location.keys())
    sorted_districts = sorted([d for d in all_districts if d != 'Sargodha'])
    if 'Sargodha' in all_districts:
        sorted_districts.insert(0, 'Sargodha')
    
    for district in sorted_districts:
        tehsil_dict = data_by_location[district]
        sorted_tehsils = sorted(tehsil_dict.keys())
        
        # Calculate district total
        district_total = 0
        district_domestic = 0
        district_commercial = 0
        
        district_teils = []
        
        for tehsil in sorted_tehsils:
            mcuc_dict = tehsil_dict[tehsil]
            sorted_mcucs = sorted(mcuc_dict.keys())
            
            # Calculate tehsil total
            tehsil_total = 0
            tehsil_domestic = 0
            tehsil_commercial = 0
            
            tehsil_mcucs = []
            
            for mcuc in sorted_mcucs:
                records = mcuc_dict[mcuc]
                color = get_marker_color(mcuc)
                domestic_count = sum(1 for r in records if str(r.get('Consumer Type', '')).strip().lower() == 'domestic')
                commercial_count = sum(1 for r in records if str(r.get('Consumer Type', '')).strip().lower() == 'commercial')
                
                # Shorten MC/UC name
                shortened_name = shorten_mcuc_name(mcuc, district, tehsil)
                
                tehsil_mcucs.append({
                    "full_name": mcuc,
                    "short_name": shortened_name,
                    "color": color,
                    "count": len(records),
                    "domestic": domestic_count,
                    "commercial": commercial_count
                })
                
                tehsil_total += len(records)
                tehsil_domestic += domestic_count
                tehsil_commercial += commercial_count
                
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
            
            district_teils.append({
                "tehsil": tehsil,
                "mcucs": tehsil_mcucs,
                "total": tehsil_total,
                "domestic": tehsil_domestic,
                "commercial": tehsil_commercial
            })
            
            district_total += tehsil_total
            district_domestic += tehsil_domestic
            district_commercial += tehsil_commercial
        
        location_groups.append({
            "district": district,
            "tehsils": district_teils,
            "total": district_total,
            "domestic": district_domestic,
            "commercial": district_commercial
        })
    
    survey_data_json = json.dumps(survey_points)
    location_data_json = json.dumps(location_groups)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Field Survey Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { 
            margin: 0; 
            padding: 0; 
            font-family: Arial, Helvetica, sans-serif;
            touch-action: manipulation;
            font-size: 14px;
        }
        #map { 
            position: absolute; 
            top: 0; 
            bottom: 0; 
            width: 100%; 
        }
        .info { 
            padding: 8px; 
            background: white; 
            background: rgba(255,255,255,0.95); 
            box-shadow: 0 0 10px rgba(0,0,0,0.3); 
            border-radius: 4px; 
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
            max-width: 320px;
            max-height: 85vh;
            overflow-y: auto;
        }
        .legend {
            background: white;
            padding: 8px;
            border-radius: 4px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            max-height: 300px;
            overflow-y: auto;
            margin-top: 8px;
        }
        .district-group {
            margin-bottom: 12px;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }
        .district-header {
            font-weight: bold;
            margin-bottom: 4px;
            color: #2c3e50;
            cursor: pointer;
            user-select: none;
            font-size: 13px;
        }
        .district-totals {
            font-size: 11px;
            color: #7f8c8d;
            margin-left: 15px;
        }
        .tehsil-group {
            margin-left: 12px;
            margin-bottom: 6px;
        }
        .tehsil-header {
            font-weight: normal;
            margin-bottom: 2px;
            color: #34495e;
            font-size: 12px;
            cursor: pointer;
            user-select: none;
        }
        .tehsil-totals {
            font-size: 10px;
            color: #95a5a6;
            margin-left: 15px;
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
            flex-shrink: 0;
        }
        .controls {
            background: white;
            padding: 8px;
            border-radius: 4px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            margin-bottom: 8px;
        }
        select, button {
            padding: 3px 5px;
            margin: 1px;
            font-size: 11px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        .filter-row {
            display: flex;
            gap: 4px;
            margin-bottom: 6px;
            flex-wrap: wrap;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-width: 100px;
        }
        .filter-label {
            font-size: 10px;
            margin-bottom: 1px;
            color: #666;
        }
        h4 {
            margin: 4px 0;
            font-size: 13px;
            color: #2c3e50;
        }
        .counts {
            font-size: 10px;
            color: #7f8c8d;
            margin-left: 4px;
        }
        .layer-control {
            margin-top: 8px;
            padding-top: 8px;
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
            font-size: 10px;
        }
        .expanded > .district-header > .toggle-icon::before,
        .expanded > .tehsil-header > .toggle-icon::before {
            content: "▼ ";
        }
        .status-bar {
            font-size: 10px;
            color: #7f8c8d;
            margin-top: 4px;
            padding: 2px;
            background: #f8f9fa;
            border-radius: 3px;
        }
        /* Mobile optimizations */
        @media (max-width: 480px) {
            .info {
                max-width: 280px;
                right: 5px;
                top: 5px;
                font-size: 13px;
            }
            select, button {
                padding: 2px 4px;
                font-size: 10px;
            }
            .filter-group {
                min-width: 80px;
            }
        }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info">
        <div class="controls">
            <div class="filter-row">
                <div class="filter-group">
                    <div class="filter-label">District</div>
                    <select id="districtFilter" onchange="populateTehsilFilter()">
                        <option value="all">All Districts</option>
''' + ''.join([f'                        <option value="{district}">{district}</option>\n' for district in sorted_districts]) + '''
                    </select>
                </div>
                <div class="filter-group">
                    <div class="filter-label">Tehsil</div>
                    <select id="tehsilFilter" onchange="populateMCUCFilter()">
                        <option value="all">All Tehsils</option>
                    </select>
                </div>
            </div>
            <div class="filter-row">
                <div class="filter-group">
                    <div class="filter-label">MC/UC</div>
                    <select id="mcucFilter">
                        <option value="all">All MC/UC</option>
                    </select>
                </div>
                <div class="filter-group">
                    <div class="filter-label">Type</div>
                    <select id="typeFilter">
                        <option value="all">All Types</option>
                        <option value="Domestic">Domestic</option>
                        <option value="Commercial">Commercial</option>
                    </select>
                </div>
            </div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
                <button onclick="applyFilters()" style="flex: 1; background: #3498db; color: white;">Apply</button>
                <button onclick="resetFilters()" style="flex: 1; background: #95a5a6; color: white;">Reset</button>
            </div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
                <button onclick="loadAllMarkers()" style="flex: 1; background: #2ecc71; color: white; font-size: 10px; padding: 4px;">Show All Markers</button>
            </div>
            
            <div class="layer-control">
                <div class="filter-label">Map Layer</div>
                <select id="layerControl" onchange="changeBaseLayer()" style="width: 100%;">
                    <option value="osm">Street Map</option>
                    <option value="satellite">Satellite</option>
                    <option value="terrain">Terrain</option>
                </select>
            </div>
            <div class="status-bar" id="statusBar">
                Ready. Select filters and click Apply.
            </div>
        </div>
        <div style="display: flex; gap: 4px; margin-top: 6px;">
            <button onclick="loadAllMarkers()" style="flex: 1; background: #2ecc71; color: white; font-size: 10px; padding: 4px;">Show All Markers</button>
        </div>
        <div class="legend">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="margin: 0;">Location Hierarchy</h4>
                <button onclick="toggleMainTable()" style="background: #ecf0f1; border: none; padding: 2px 6px; font-size: 10px; cursor: pointer;" id="collapseBtn">Collapse</button>
            </div>
''' + ''.join([f'''            <div class="district-group" id="district-{i}">
                <div class="district-header" onclick="toggleCollapse(this.parentNode)">
                    <span class="toggle-icon"></span>{district_group["district"]}
                </div>
                <div class="district-totals">Total: {district_group["total"]}, Dom: {district_group["domestic"]}, Com: {district_group["commercial"]}</div>
                <div class="collapsible-content">
''' + ''.join([f'''                    <div class="tehsil-group" id="tehsil-{j}">
                        <div class="tehsil-header" onclick="toggleCollapse(this.parentNode)">
                            <span class="toggle-icon"></span>{tehsil_group["tehsil"]}
                        </div>
                        <div class="tehsil-totals">Total: {tehsil_group["total"]}, Dom: {tehsil_group["domestic"]}, Com: {tehsil_group["commercial"]}</div>
                        <div class="collapsible-content">
''' + ''.join([f'                            <div class="legend-item"><div class="legend-color" style="background-color:{mcuc["color"]};"></div>{mcuc["short_name"]} <span class="counts">({mcuc["count"]}, Dom:{mcuc["domestic"]}, Com:{mcuc["commercial"]})</span></div>\n' for mcuc in tehsil_group["mcucs"]]) + '''                        </div>
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
        // Initialize the map with better defaults
        var map = L.map('map', {
            zoomControl: true,
            doubleClickZoom: true,
            scrollWheelZoom: true,
            touchZoom: true,
            inertia: true,
            inertiaDeceleration: 3000,
            maxBoundsViscosity: 1.0
        }).setView([32.0833, 72.6667], 11);
        
        // Base layers
        var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18,
            tileSize: 256
        });
        
        var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri',
            maxZoom: 18,
            tileSize: 256
        });
        
        var terrainLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri',
            maxZoom: 18,
            tileSize: 256
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
        
        // Performance settings
        var MAX_MARKERS = 10000;
        var currentMarkerCount = 0;
        
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
                // Add all unique tehsils
                var addedTehsils = new Set();
                locationData.forEach(function(districtGroup) {
                    districtGroup.tehsils.forEach(function(tehsil) {
                        if (!addedTehsils.has(tehsil.tehsil)) {
                            addedTehsils.add(tehsil.tehsil);
                            var option = document.createElement('option');
                            option.value = tehsil.tehsil;
                            option.text = tehsil.tehsil;
                            tehsilSelect.appendChild(option);
                        }
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
            updateStatusBar();
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
                // If "All Tehsils" selected
                if (selectedDistrict === 'all') {
                    // Show all MC/UCs
                    locationData.forEach(function(districtGroup) {
                        districtGroup.tehsils.forEach(function(tehsil) {
                            tehsil.mcucs.forEach(function(mcuc) {
                                var option = document.createElement('option');
                                option.value = mcuc.full_name;
                                option.text = mcuc.short_name;
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
                                    option.value = mcuc.full_name;
                                    option.text = mcuc.short_name;
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
                                    option.value = mcuc.full_name;
                                    option.text = mcuc.short_name;
                                    mcucSelect.appendChild(option);
                                });
                            }
                        });
                    }
                });
            }
            updateStatusBar();
        }
        
        // Function to toggle collapsible sections
        function toggleCollapse(element) {
            element.classList.toggle('expanded');
        }
        
        // Function to update status bar
        function updateStatusBar(message) {
            var statusBar = document.getElementById('statusBar');
            if (message) {
                statusBar.textContent = message;
            }
        }
        
        // Function to create markers with filters
        function createMarkers(filterDistrict = 'all', filterTehsil = 'all', filterMCUC = 'all', filterType = 'all') {
            updateStatusBar('Loading markers...');
            
            // Clear existing markers
            markers.clearLayers();
            
            // Counter for performance
            var markerCount = 0;
            var bounds = [];
            
            // Process each survey point
            surveyData.some(function(survey) {
                // Skip if filtering by district and district doesn't match
                if (filterDistrict !== 'all' && survey.district.trim() !== filterDistrict.trim()) {
                    return false;
                }
                
                // Skip if filtering by tehsil and tehsil doesn't match
                if (filterTehsil !== 'all' && survey.tehsil.trim() !== filterTehsil.trim()) {
                    return false;
                }
                
                // Skip if filtering by MC/UC and MC/UC doesn't match
                // When filterMCUC is 'all', we show all MC/UCs for the selected district/tehsil
                if (filterMCUC !== 'all' && filterMCUC !== '' && filterMCUC !== null && filterMCUC !== undefined) {
                    if (survey.mc_uc.trim() !== filterMCUC.trim()) {
                        return false;
                    }
                }
                
                // Skip if filtering by consumer type and type doesn't match
                if (filterType !== 'all' && survey.consumer_type.trim().toLowerCase() !== filterType.trim().toLowerCase()) {
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
                    '<b>ID:</b> ' + survey.survey_id + '<br>' +
                    '<b>District:</b> ' + survey.district + '<br>' +
                    '<b>Tehsil:</b> ' + survey.tehsil + '<br>' +
                    '<b>MC/UC:</b> ' + survey.mc_uc + '<br>' +
                    '<b>Type:</b> ' + survey.consumer_type + '<br>' +
                    '<b>House:</b> ' + survey.house_type + '<br>' +
                    '<b>Date:</b> ' + survey.survey_date;
                
                // Get color for this MC/UC
                var color = survey.color || '#3388ff';
                
                // Create circle marker
                var marker = L.circleMarker([lat, lng], {
                    radius: 5,
                    fillColor: color,
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                }).bindPopup(popupContent);
                
                // Add to map
                marker.addTo(markers);
                markerCount++;
                bounds.push([lat, lng]);
                
                // Performance limit
                if (markerCount >= MAX_MARKERS) {
                    updateStatusBar('Loaded ' + markerCount + ' markers (limit reached: ' + MAX_MARKERS + ')');
                    return true; // Break the loop
                }
                
                return false; // Continue loop
            });
            
            currentMarkerCount = markerCount;

            // Count total markers that match current filters (without limit)
            var totalCount = 0;
            surveyData.forEach(function(survey) {
                // Skip if filtering by district and district doesn't match
                if (filterDistrict !== 'all' && survey.district.trim() !== filterDistrict.trim()) {
                    return;
                }
                
                // Skip if filtering by tehsil and tehsil doesn't match
                if (filterTehsil !== 'all' && survey.tehsil.trim() !== filterTehsil.trim()) {
                    return;
                }
                
                // Skip if filtering by MC/UC and MC/UC doesn't match
                if (filterMCUC !== 'all' && survey.mc_uc.trim() !== filterMCUC.trim()) {
                    return;
                }
                
                // Skip if filtering by consumer type and type doesn't match
                if (filterType !== 'all' && survey.consumer_type.trim().toLowerCase() !== filterType.trim().toLowerCase()) {
                    return;
                }
                
                totalCount++;
            });
            
            if (markerCount === totalCount) {
                updateStatusBar('Loaded ' + markerCount + ' markers (all matching filters)');
            } else {
                updateStatusBar('Loaded ' + markerCount + ' markers (limited display, ' + totalCount + ' total matching filters)');
            }
            
            // Smart zoom handling
            if (bounds.length > 0) {
                var boundsGroup = L.latLngBounds(bounds);
                if (filterMCUC !== 'all') {
                    // If specific MC/UC selected, fit tightly
                    map.fitBounds(boundsGroup, {padding: [20, 20]});
                } else if (filterTehsil !== 'all') {
                    // If specific tehsil selected, fit with moderate padding
                    map.fitBounds(boundsGroup, {padding: [50, 50]});
                } else if (filterDistrict !== 'all') {
                    // If specific district selected, fit with more padding
                    map.fitBounds(boundsGroup, {padding: [100, 100]});
                } else {
                    // If "All" selected, maintain reasonable zoom level
                    var currentZoom = map.getZoom();
                    // Only zoom if we have a good number of markers
                    if (markerCount > 10) {
                        map.fitBounds(boundsGroup, {padding: [50, 50]});
                    } else if (currentZoom < 11) {
                        // Don't zoom out too far if we have few markers
                        map.setZoom(Math.max(currentZoom, 11));
                    }
                }
            } else {
                updateStatusBar('No markers found for selected filters');
            }
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
            map.setView([32.0833, 72.6667], 11);
            markers.clearLayers();
            currentMarkerCount = 0;
            updateStatusBar('Filters reset. Select and apply to load data.');
        }
        
        // Initialize filters - default to Sargodha district and Sargodha tehsil
        document.getElementById('districtFilter').value = 'Sargodha';
        populateTehsilFilter();
        // Set tehsil to Sargodha
        document.getElementById('tehsilFilter').value = 'Sargodha';
        populateMCUCFilter();
        // Apply filters to show initial data
        applyFilters();
        
        // Don't load any markers initially for performance
        updateStatusBar('Ready. Select filters and click Apply.');
        
        // Function to load all markers without limit
        function loadAllMarkers() {
            var originalMaxMarkers = MAX_MARKERS;
            MAX_MARKERS = surveyData.length; // Set to total number of records
            applyFilters();
            MAX_MARKERS = originalMaxMarkers; // Restore original limit
        }
        

        
        // Function to toggle main table visibility
        function toggleMainTable() {
            var infoPanel = document.querySelector('.info');
            var legend = document.querySelector('.legend');
            var controls = document.querySelector('.controls');
            var btn = document.getElementById('collapseBtn');
            
            if (legend && controls && legend.style.display === 'none') {
                // Expand the panel
                legend.style.display = 'block';
                controls.style.display = 'block';
                btn.textContent = 'Collapse';
            } else if (legend && controls) {
                // Collapse the panel but keep a small expand button
                legend.style.display = 'none';
                controls.style.display = 'none';
                btn.textContent = 'Expand Panel';
            }
        }
        
        // Function to create a floating expand button when panel is collapsed
        function createFloatingExpandButton() {
            // Check if button already exists
            if (document.getElementById('floatingExpandBtn')) return;
            
            var expandBtn = document.createElement('button');
            expandBtn.id = 'floatingExpandBtn';
            expandBtn.textContent = '☰ Expand Panel';
            expandBtn.style.position = 'fixed';
            expandBtn.style.top = '10px';
            expandBtn.style.right = '10px';
            expandBtn.style.zIndex = '1001';
            expandBtn.style.background = '#3498db';
            expandBtn.style.color = 'white';
            expandBtn.style.border = 'none';
            expandBtn.style.padding = '5px 10px';
            expandBtn.style.borderRadius = '4px';
            expandBtn.style.cursor = 'pointer';
            expandBtn.style.fontSize = '12px';
            expandBtn.onclick = function() {
                toggleMainTable();
                document.body.removeChild(expandBtn);
            };
            
            document.body.appendChild(expandBtn);
        }
        
        // Override toggleMainTable to also handle floating button
        var originalToggleMainTable = toggleMainTable;
        toggleMainTable = function() {
            var legend = document.querySelector('.legend');
            var controls = document.querySelector('.controls');
            var btn = document.getElementById('collapseBtn');
            
            if (legend && controls && legend.style.display === 'none') {
                // Expand the panel
                legend.style.display = 'block';
                controls.style.display = 'block';
                btn.textContent = 'Collapse';
                // Remove floating button if it exists
                var floatingBtn = document.getElementById('floatingExpandBtn');
                if (floatingBtn) {
                    document.body.removeChild(floatingBtn);
                }
            } else if (legend && controls) {
                // Collapse the panel
                legend.style.display = 'none';
                controls.style.display = 'none';
                btn.textContent = 'Expand Panel';
                // Create floating button
                createFloatingExpandButton();
            }
        };
        
        // Initialize with table expanded as per project configuration
        document.addEventListener('DOMContentLoaded', function() {
            var legend = document.querySelector('.legend');
            legend.style.display = 'block';
            document.getElementById('collapseBtn').textContent = 'Collapse';
        });
    </script>
</body>
</html>'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated final optimized map file: {output_file}")

def process_csv_files():
    """Process CSV files and generate map data"""
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
            required_columns = ['Latitude', 'Longitude', 'District', 'Tehsil', 'Union Council']
            if not all(col in df.columns for col in required_columns):
                print(f"Skipping {csv_file} - missing required columns")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                # Skip if location is missing
                lat = str(row.get('Latitude', '')).strip()
                lon = str(row.get('Longitude', '')).strip()
                if not lat or not lon or lat == '' or lon == '':
                    continue
                # Create location string in the format expected by the map
                location_str = f"{lat},{lon}"
                
                # Create identifiers
                district = str(row.get('District', '')).strip()
                tehsil = str(row.get('Tehsil', '')).strip()
                uc = str(row.get('Union Council', '')).strip()
                
                # Create MC/UC identifier
                mc_uc = f"{district} - {uc}" if uc else f"{district} - {tehsil}"
                
                # Add location string to the row data
                row_dict = dict(row)
                row_dict['Location'] = location_str
                
                # Add to collection
                data_by_location[district][tehsil][mc_uc].append(row_dict)
                
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
    print("  Final Optimized Field Staff Map Generator")
    print("==============================================\n")
    
    process_csv_files()
    
    print("\n==============================================")
    print("  Map Generation Complete!")
    print("  Features:")
    print("  - District/tehsil totals in hierarchy")
    print("  - Shortened MC/UC names")
    print("  - Format: Total, Dom:Number, Com:Number")
    print("  - Special Sargodha naming (MC-1, MC-2, etc.)")
    print("  - Smart zoom control")
    print("  - Mobile-optimized interface")
    print("==============================================")

if __name__ == "__main__":
    main()