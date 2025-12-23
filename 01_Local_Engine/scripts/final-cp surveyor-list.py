#!/usr/bin/env python3
"""
Final optimized field staff map generator with improved naming and formatting.
Includes date filtering functionality, credits, and surveyor name in tooltips.
Fixed button visibility issues.
"""

import pandas as pd
import os
import json
import re
from collections import defaultdict

# Define input folder
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), "..", "outputs", "scraped_data")

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
    """Generate optimized HTML file with improved naming and surveyor info"""
    
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
                    # Collect all image URLs
                    image_urls = []
                    for i in range(1, 5):  # Image URL 1 through 4
                        url = str(record.get(f'Image URL {i}', '')).strip()
                        if url:
                            image_urls.append(url)
                    
                    survey_points.append({
                        'survey_id': str(record.get('Survey ID', '')),
                        'district': district,
                        'tehsil': tehsil,
                        'mc_uc': mcuc,
                        'consumer_type': str(record.get('Consumer Type', '')).strip(),
                        'consumer_name': str(record.get('Name', '')).strip(),
                        'consumer_address': str(record.get('Address', '')).strip(),
                        'uc_type': str(record.get('UC Type', '')).strip(),
                        'level': str(record.get('Level', '')).strip(),
                        'survey_type': str(record.get('Type', '')).strip(),
                        'house_type': str(record.get('House Type', '')).strip(),
                        'survey_date': str(record.get('Survey Date', '')).strip(),
                        'survey_time': str(record.get('Survey Time', '')).strip(),
                        'surveyor_name': str(record.get('Surveyor Name', '')).strip(),
                        'location': str(record.get('Location', '')).strip(),
                        'image_urls': image_urls,
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
    
    # Properly escape JSON data for JavaScript embedding
    survey_data_json = json.dumps(survey_points).replace('\\', '\\\\').replace('"', '\\"')
    location_data_json = json.dumps(location_groups).replace('\\', '\\\\').replace('"', '\\"')
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Field Survey Map - SGD-BHL-KSB TMT</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        body { 
            margin: 0; 
            padding: 0; 
            font-family: 'Roboto', sans-serif;
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
            background: rgba(255,255,255,0.98); 
            box-shadow: 0 8px 32px rgba(0,0,0,0.2); 
            border-radius: 12px; 
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
        select, button, input[type="date"] {
            padding: 10px 14px;
            margin: 4px;
            font-size: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-family: 'Roboto', sans-serif;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        select:focus, button:focus, input:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
        }
        button {
            cursor: pointer;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        button:active {
            transform: translateY(1px);
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
            font-size: 13px;
            color: #2c3e50;
            font-weight: bold;
            margin-top: 4px;
            padding: 4px;
            background: #f8f9fa;
            border-radius: 3px;
            border: 1px solid #e0e0e0;
        }
        .credits {
            font-size: 10px;
            color: #7f8c8d;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            padding-top: 4px;
            border-top: 1px solid #eee;
        }
        .map-title {
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
            color: #2c3e50;
            padding-bottom: 4px;
            border-bottom: 1px solid #eee;
        }
        /* Floating expand button */
        #floatingExpandBtn {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1001;
            background: #3498db;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: none; /* Hidden by default */
        }
        /* List View Overhaul */
        #listModal {
            background-color: #f0f2f5;
        }

        .explorer-container {
            display: flex;
            height: 100vh;
            width: 100%;
            background: #fff;
            overflow: hidden;
        }

        .explorer-sidebar {
            flex: 0 0 320px;
            height: 100%;
            border-right: 1px solid #e2e8f0;
            overflow-y: auto;
            background: #fff;
            z-index: 5;
            padding-bottom: 100px;
        }

        .explorer-sidebar table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }

        .explorer-sidebar th, .explorer-sidebar td {
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid #f1f5f9;
        }

        .list-row {
            cursor: pointer !important;
            transition: all 0.2s;
            border-left: 4px solid transparent;
            width: 100%;
        }

        .list-row:hover {
            background: #f7fafc;
        }

        .list-row.active {
            background: #e6fffa !important;
            border-left: 4px solid #38b2ac;
        }

        .list-row.active td {
            color: #234e52;
            font-weight: 600;
        }

        .explorer-main {
            flex: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: #f8fafc;
        }

        .explorer-main-header {
            padding: 30px 40px;
            padding-right: 80px; /* Space for the fixed close button */
            background: #fff;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            flex-direction: column;
            gap: 20px;
            flex-shrink: 0;
        }

        .header-top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-search-row {
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }

        .explorer-content-area {
            flex: 1;
            overflow-y: auto;
            padding: 30px 40px;
        }

        .detail-split-content {
            display: flex;
            gap: 40px;
            width: 100%;
            align-items: flex-start;
        }

        .detail-info-column {
            flex: 2;
            min-width: 350px;
        }

        .detail-gallery-column {
            flex: 0 0 240px;
            max-width: 250px;
        }

        /* Typography & Components */
        .detail-title {
            font-size: 22px;
            font-weight: 700;
            color: #1a202c;
            letter-spacing: -0.5px;
        }

        .detail-subtitle {
            font-size: 13px;
            color: #718096;
            margin-top: 4px;
        }

        .detail-info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            background: #fff;
            padding: 25px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .info-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .info-label {
            font-size: 11px;
            color: #a0aec0;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.05em;
        }

        .info-value {
            font-size: 14px;
            color: #2d3748;
            font-weight: 500;
        }

        .highlight-blue {
            color: #3182ce;
            font-weight: 800;
            font-size: 20px;
        }

        .highlight-dark {
            color: #1a202c;
            font-weight: 700;
            font-size: 15px;
        }

        .explorer-gallery {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .counter-badge {
            background: #ebf8ff;
            color: #2b6cb0;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            border: 1px solid #bee3f8;
            margin-left: 10px;
        }

        #activeFilterInfo {
            font-size: 12px;
            color: #64748b;
            font-weight: 500;
            margin-left: auto; /* Push to right on desktop */
        }

        .explorer-thumb {
            width: 100%;
            height: auto;
            aspect-ratio: 4/3;
            object-fit: cover;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid #e2e8f0;
        }

        /* Mobile Adjustments */
        @media (max-width: 1024px) {
            .detail-split-content {
                flex-direction: column-reverse; /* Put info below gallery on tablets if needed */
            }
            .detail-info-column, .detail-gallery-column {
                width: 100%;
                max-width: 100%;
                min-width: unset;
                flex: none;
            }
        }

        @media (max-width: 768px) {
            .explorer-sidebar {
                flex: 0 0 120px; /* Wider for mobile ID visibility */
                padding-bottom: 80px;
            }
            .explorer-sidebar table th, 
            .explorer-sidebar table td:not(:first-child) {
                display: none;
            }
            .explorer-sidebar td:first-child {
                text-align: center;
                padding: 15px 10px; /* Increased padding */
            }
            .explorer-main-header {
                padding: 15px 15px;
                padding-right: 60px;
                gap: 12px;
            }
            .header-search-row {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            .header-search-row > div {
                max-width: 100% !important;
                width: 100%;
            }
            .explorer-actions {
                top: 0;
                right: 0;
                padding: 0;
                background: #cbd5e0;
                border-bottom-left-radius: 6px;
            }
            .close-btn-modern {
                width: 24px;
                height: 24px;
                font-size: 16px;
            }
            .detail-map-btn {
                padding: 0 6px;
                font-size: 9px;
                height: 24px;
            }
            .explorer-content-area {
                padding: 10px;
            }
            .detail-info-grid {
                padding: 12px;
                gap: 12px;
            }
            .detail-title {
                font-size: 16px;
            }
            .explorer-gallery {
                flex-direction: row;
                flex-wrap: wrap;
                gap: 8px;
            }
            .explorer-thumb {
                width: calc(33.33% - 6px);
                aspect-ratio: 1/1;
                border-radius: 8px;
            }
            .detail-title {
                font-size: 18px;
            }
        }

        @media (max-width: 480px) {
            .info {
                max-width: 280px;
                right: 5px;
                top: 5px;
                font-size: 13px;
            }
            select, button, input[type="date"] {
                padding: 2px 4px;
                font-size: 10px;
            }
            .filter-group {
                min-width: 80px;
            }
        }
        
        /* Image Viewer Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 4000; /* Higher than list modal */
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.98);
            overflow: hidden;
            touch-action: pinch-zoom;
        }
        
        .modal-content {
            position: relative;
            margin: auto;
            padding: 0;
            width: 90%;
            max-width: 900px;
            height: 90vh;
            top: 50%;
            transform: translateY(-50%);
            text-align: center;
        }
        
        .modal-image {
            max-width: 100%;
            max-height: 80vh;
            object-fit: contain;
            border: 2px solid white;
            transform-origin: center center;
            transition: transform 0.3s ease;
            cursor: grab;
        }
        
        .explorer-actions {
            position: absolute;
            top: 0;
            right: 0;
            display: flex;
            align-items: stretch; /* Make children match height */
            gap: 1px; /* Subtle line between buttons */
            z-index: 5000;
            padding: 0;
            background: #cbd5e0; /* Border color for the gap */
            border-bottom-left-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .close-btn-modern {
            width: 28px;
            height: 28px;
            border-radius: 0;
            border: none;
            background: #fff;
            color: #e53e3e;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 16px;
            font-weight: 300;
            position: relative;
        }

        .detail-map-btn {
            background: #2d3748;
            color: #fff;
            border: none;
            padding: 0 8px;
            border-radius: 0;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: none;
            align-items: center;
            gap: 4px;
            height: 28px; /* Smaller than close btn */
        }

        .close-btn-modern:hover {
            background: #fdf2f2;
        }

        .detail-map-btn:hover {
            background: #1a202c;
        }
        
        /* Image Viewer Specific Close Button */
        #imageModal .close-btn-modern {
            position: absolute;
            top: 25px;
            right: 25px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.4);
            color: #fff;
            font-size: 30px;
            backdrop-filter: blur(5px);
        }

        #imageModal .close-btn-modern:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.1);
        }

        .prev, .next {
            cursor: pointer;
            position: absolute;
            top: 50%;
            width: auto;
            padding: 20px;
            margin-top: -50px;
            color: white;
            font-weight: bold;
            font-size: 24px;
            transition: 0.6s ease;
            border-radius: 0 3px 3px 0;
            user-select: none;
            -webkit-user-select: none;
            background: rgba(0,0,0,0.3);
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            min-width: 50px;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .next {
            right: 0;
            border-radius: 3px 0 0 3px;
        }
        
        .prev:hover, .next:hover {
            background: rgba(0,0,0,0.8);
        }
        
        .image-counter {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 16px;
            padding: 10px;
            background-color: rgba(0,0,0,0.5);
            border-radius: 5px;
        }
        
        .thumbnail-strip {
            position: absolute;
            bottom: 60px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 5px;
            max-width: 80%;
            overflow-x: auto;
            padding: 5px;
        }
        
        .thumbnail {
            width: 50px;
            height: 50px;
            object-fit: cover;
            border: 2px solid transparent;
            cursor: pointer;
            opacity: 0.7;
        }
        
        .thumbnail.active {
            border-color: white;
            opacity: 1;
        }
        
        .thumbnail:hover {
            opacity: 1;
        }
        
        /* Stats Table Styling */

        .stats-container {

            padding: 20px;

            background: white;

        }

        .stats-table {

            width: 100%;

            border-collapse: collapse;

            margin-top: 15px;

            background: white;

            border-radius: 8px;

            overflow: hidden;

            box-shadow: 0 1px 3px rgba(0,0,0,0.1);

        }

        .stats-table th {

            background: #2c3e50;

            color: white;

            text-align: left;

            padding: 12px;

            font-size: 13px;

        }

        .stats-table td {

            padding: 10px 12px;

            border-bottom: 1px solid #eee;

            font-size: 13px;

        }

        .stats-table tr:nth-child(even) {

            background: #f8f9fa;

        }

        .stats-table tr:hover {

            background: #f1f4f6;

        }

        .rank-badge {

            background: #3498db;

            color: white;

            padding: 2px 8px;

            border-radius: 10px;

            font-size: 11px;

            font-weight: bold;

        }

        .image-controls {
            position: absolute;
            top: 20px;
            left: 20px;
            color: white;
            z-index: 2001;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            max-width: calc(100% - 100px);
        }
        
        .control-btn {
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            padding: 12px 16px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;
            min-width: 44px; /* Minimum touch target size */
            min-height: 44px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        
        .control-btn:hover {
            background: rgba(0,0,0,0.8);
        }
        
        /* Mobile-specific adjustments */
        @media (max-width: 768px) {
            .control-btn {
                padding: 14px 18px;
                font-size: 20px;
                min-width: 50px;
                min-height: 50px;
            }
            
            .prev, .next {
                padding: 20px 15px;
                font-size: 24px;
            }
            
            .image-controls {
                top: 15px;
                left: 15px;
                gap: 8px;
            }
            
            .close {
                top: 15px;
                right: 15px;
            }
            
            /* Center image in mobile view */
            .modal-content {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .modal-image {
                max-height: 70vh;
            }
        }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <!-- Floating Expand Button (Hidden by default) -->
    <button id="floatingExpandBtn" onclick="expandPanel()">☰ Expand Panel</button>
    
    <!-- Image Viewer Modal -->
    <div id="imageModal" class="modal" style="z-index: 5000;">
        <button class="close-btn-modern" onclick="closeImageViewer()" style="z-index: 5100;">×</button>
        <a class="prev" onclick="changeImage(-1)">&#10094;</a>
        <a class="next" onclick="changeImage(1)">&#10095;</a>
        <div class="modal-content">
            <img class="modal-image" id="modalImage" src="" alt="">
            <div class="image-counter" id="imageCounter"></div>
            <div class="thumbnail-strip" id="thumbnailStrip"></div>
        </div>
        <!-- Image Controls -->
        <div class="image-controls">
            <button class="control-btn" onclick="zoomImage(1.2)">+</button>
            <button class="control-btn" onclick="zoomImage(0.8)">-</button>
            <button class="control-btn" onclick="rotateImage(-90)">↺</button>
            <button class="control-btn" onclick="rotateImage(90)">↻</button>
            <button class="control-btn" onclick="resetImageTransform()">Reset</button>
        </div>
    </div>
    
    <!-- List View Modal -->
    <div id="listModal" class="modal" style="z-index: 2000;">
        <div class="explorer-actions">
            <button id="detailMapBtn" class="detail-map-btn" onclick="// set by JS">Map</button>
            <button class="close-btn-modern" onclick="closeListView()" style="z-index: 2100;">×</button>
        </div>
        <div class="explorer-container">
            <div id="explorerSidebar" class="explorer-sidebar">
                <!-- List rows injected here -->
            </div>
            <div class="explorer-main">
                <div id="explorerMainHeader" class="explorer-main-header">
                    <div class="header-top-row">
                        <div id="modalTitleArea">
                            <h2 style="margin: 0; font-size: 20px; color: #1a202c; display: flex; align-items: center; gap: 12px;">
                                <span id="listTitleText">Filtered Records</span>
                                <span id="searchCount" class="counter-badge"></span>
                            </h2>
                            <div id="listSubtitle" style="font-size: 13px; color: #718096; margin-top: 4px;">Showing all matching records from current search</div>
                        </div>
                    </div>
                    <div class="header-search-row">
                        <div style="flex: 1; max-width: 400px; position: relative;">
                            <input type="text" id="listSearch" placeholder="Search ID, location, or surveyor..." 
                                   style="width: 100%; padding: 12px 20px; padding-left: 45px; border-radius: 12px; border: 1px solid #e2e8f0; font-size: 14px; background: #f8fafc;"
                                   onkeyup="filterList()">
                            <span style="position: absolute; left: 18px; top: 50%; transform: translateY(-50%); color: #a0aec0; font-size: 16px;">🔍</span>
                        </div>
                        <div id="activeFilterInfo" style="font-size: 12px; color: #64748b; font-weight: 500;"></div>
                    </div>
                </div>
                <div class="explorer-content-area">
                    <div id="explorerDetail">
                        <div style="text-align: center; color: #94a3b8; margin-top: 80px;">
                            <div style="font-size: 60px; margin-bottom: 20px;">📋</div>
                            <div style="font-size: 18px; font-weight: 600; color: #475569;">Select a Record</div>
                            <div style="font-size: 14px; margin-top: 8px;">Pick a survey from the sidebar to view full details and gallery</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Surveyor Stats Modal -->
    <div id="statsModal" class="modal" style="z-index: 3000;">
        <div class="explorer-actions">
            <button class="close-btn-modern" onclick="closeStatsView()">×</button>
        </div>
        <div class="explorer-container" style="flex-direction: column; overflow-y: auto;">
            <div class="explorer-main-header">
                <h2 style="margin: 0; font-size: 20px; color: #1a202c;">Surveyor Performance Summary</h2>
                <div id="statsSubtitle" style="font-size: 13px; color: #718096; margin-top: 4px;">Based on current filters and date range</div>
            </div>
            <div class="stats-container" id="statsContent">
                <!-- Table will be injected here -->
            </div>
        </div>
    </div>
    
    <div class="info" id="infoPanel">
        <div class="map-title">Survey Data (SGD-BHL-KSB) TMT</div>
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
            <!-- Date Filter Row -->
            <div class="filter-row">
                <div class="filter-group">
                    <div class="filter-label">Start Date</div>
                    <input type="date" id="startDateFilter" onchange="updateDateRange()">
                </div>
                <div class="filter-group">
                    <div class="filter-label">End Date</div>
                    <input type="date" id="endDateFilter" onchange="updateDateRange()">
                </div>
            </div>
            <!-- Date Preset Buttons -->
            <div style="display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap;">
                <button onclick="setDateRange('today')" style="flex: 1; font-size: 10px; padding: 4px;">Today</button>
                <button onclick="setDateRange('week')" style="flex: 1; font-size: 10px; padding: 4px;">This Week</button>
                <button onclick="setDateRange('month')" style="flex: 1; font-size: 10px; padding: 4px;">This Month</button>
                <button onclick="clearDateRange()" style="flex: 1; font-size: 10px; padding: 4px; background: #e74c3c;">Clear Dates</button>
            </div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
                <button onclick="applyFilters()" style="flex: 1; background: #3498db; color: white;">Apply</button>
                <button onclick="resetFilters()" style="flex: 1; background: #95a5a6; color: white;">Reset</button>
            </div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
                <button onclick="loadAllMarkers()" style="flex: 1.5; background: #2ecc71; color: white; font-size: 11px; padding: 10px; border: none;">Show All</button>
                <button onclick="showListView()" style="flex: 1; background: #f39c12; color: white; font-size: 11px; padding: 10px; border: none;">View List</button>
                <!-- New Button -->
                <button onclick="showSurveyorStats()" style="flex: 1.5; background: #9b59b6; color: white; font-size: 11px; padding: 10px; border: none; box-shadow: 0 4px 6px rgba(155, 89, 182, 0.3);">Surveyor Stats</button>
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
        <div class="legend">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="margin: 0;">Location Hierarchy</h4>
                <button onclick="collapsePanel()" style="background: #ecf0f1; border: none; padding: 2px 6px; font-size: 10px; cursor: pointer;" id="collapseBtn">Collapse</button>
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
        <div class="credits">
            <div id="zoom-level">Zoom Level: 11</div>
            <div>Map created by Kashif Khalil</div>
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
        
        // Update zoom level display
        map.on('zoomend', function() {
            document.getElementById('zoom-level').textContent = 'Zoom Level: ' + map.getZoom();
        });
        
        // Survey data - parse JSON string back to object
        var surveyData = JSON.parse("''' + survey_data_json + '''");
        
        // Location data for filtering - parse JSON string back to object
        var locationData = JSON.parse("''' + location_data_json + '''");        
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
                                    option.text = tehsil.tehsil + ' - ' + mcuc.full_name;
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
                                    option.text = mcuc.full_name;
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
        
        // Date utility functions
        function parseDate(dateString) {
            // Handle various date formats
            if (!dateString) return null;
            
            // Try ISO format first (YYYY-MM-DD)
            let date = new Date(dateString);
            if (!isNaN(date.getTime())) return date;
            
            // Try other common formats
            // Add more formats as needed based on your data
            return null;
        }
        
        // Add this function to update date range display
        function updateDateRange() {
            // Optional: Update UI to show selected date range
            const startDate = document.getElementById('startDateFilter').value;
            const endDate = document.getElementById('endDateFilter').value;
            
            if (startDate || endDate) {
                let rangeText = "Date Range: ";
                if (startDate) rangeText += startDate;
                else rangeText += "Start";
                rangeText += " to ";
                if (endDate) rangeText += endDate;
                else rangeText += "End";
            }
        }
        
        // Add these helper functions
        function setDateRange(range) {
            const today = new Date();
            let startDate = new Date();
            
            if (range === 'today') {
                startDate = today;
            } else if (range === 'week') {
                startDate.setDate(today.getDate() - 7);
            } else if (range === 'month') {
                startDate.setMonth(today.getMonth() - 1);
            }
            
            // Format dates as YYYY-MM-DD for input fields
            const formatDate = (date) => {
                return date.toISOString().split('T')[0];
            };
            
            document.getElementById('startDateFilter').value = formatDate(startDate);
            document.getElementById('endDateFilter').value = formatDate(today);
            
            // Trigger update
            updateDateRange();
            applyFilters();
        }
        
        function clearDateRange() {
            document.getElementById('startDateFilter').value = '';
            document.getElementById('endDateFilter').value = '';
            updateDateRange();
            applyFilters();
        }
        
        // Function to create markers with filters
        function createMarkers(filterDistrict = 'all', filterTehsil = 'all', filterMCUC = 'all', filterType = 'all') {
            // Get date filter values
            const startDateStr = document.getElementById('startDateFilter').value;
            const endDateStr = document.getElementById('endDateFilter').value;
            
            const startDate = startDateStr ? new Date(startDateStr) : null;
            const endDate = endDateStr ? new Date(endDateStr) : null;
            
            updateStatusBar('Loading markers...');
            
            // Clear existing markers
            markers.clearLayers();
            currentFilteredSurveys = []; // Reset tracked filtered data
            
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
                
                // Date filtering
                // Skip if filtering by date and survey date is outside range
                if (startDate || endDate) {
                    const surveyDate = parseDate(survey.survey_date);
                    if (surveyDate) {
                        // Normalize dates to ignore time component
                        const normalizedSurveyDate = new Date(surveyDate.getFullYear(), surveyDate.getMonth(), surveyDate.getDate());
                        
                        if (startDate && normalizedSurveyDate < new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate())) {
                            return false; // Skip - before start date
                        }
                        if (endDate && normalizedSurveyDate > new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate())) {
                            return false; // Skip - after end date
                        }
                    }
                    // If we can't parse the date, we might want to skip or include based on requirements
                    // For now, we'll skip records with unparseable dates when date filtering is active
                    else if (startDate || endDate) {
                        return false; // Skip records with unparseable dates
                    }
                }
                
                // Parse location
                var coords = survey.location.split(',');
                if (coords.length !== 2) return false;
                
                var lat = parseFloat(coords[0]);
                var lng = parseFloat(coords[1]);
                
                if (isNaN(lat) || isNaN(lng)) return false;
                
                // Create popup content with multiple image thumbnails
                var imageUrls = survey.image_urls || [];
                var popupContent = 
                    '<b>ID:</b> ' + survey.survey_id + '<br>' +
                    '<b>Tehsil:</b> ' + survey.tehsil + '<br>' +
                    '<b>MC/UC:</b> ' + survey.mc_uc + '<br>' +
                    '<b>Type:</b> ' + survey.consumer_type + '<br>' +
                    '<b>House:</b> ' + survey.house_type + '<br>' +
                    '<b>Surveyor:</b> ' + (survey.surveyor_name || 'N/A') + '<br>' +
                    '<b>Date:</b> ' + survey.survey_date;
                
                // Add image thumbnails if available
                if (imageUrls.length > 0) {
                    popupContent += '<br><div style="margin-top: 8px;"><b>Images (' + imageUrls.length + '):</b><br>';
                    
                    // Add thumbnails (up to 4 for performance)
                    var maxThumbnails = Math.min(imageUrls.length, 4);
                    for (var i = 0; i < maxThumbnails; i++) {
                        var imageUrl = imageUrls[i];
                        if (imageUrl && imageUrl.trim() !== '') {
                            popupContent += '<div style="display: inline-block; margin: 2px;">' +
                                '<img src="' + imageUrl + '" style="width: 50px; height: 50px; object-fit: cover; border: 1px solid #ccc; cursor: pointer;" alt="Survey Image ' + (i+1) + '" title="Click to view" onclick="openImageViewer(' + JSON.stringify(imageUrls).replace(/"/g, '&quot;') + ', ' + i + ')">' +
                                '</div>';
                        }
                    }
                    
                    // Add count indicator if there are more images
                    if (imageUrls.length > 4) {
                        popupContent += '<div style="font-size: 10px; color: #666; margin-top: 4px;">+' + (imageUrls.length - 4) + ' more images</div>';
                    }
                    
                    popupContent += '</div>';
                }
                
                // Get color for this MC/UC
                var color = survey.color || '#3388ff';
                
                // Create circle marker
                var marker = L.circleMarker([lat, lng], {
                    radius: 5,
                    fillColor: color,
                    color: "#000",
                    weight: 1,
                    opacity: 0.6,
                    fillOpacity: 0.5
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
            currentFilteredSurveys = []; // Populate everything matching the filters for the list view
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
                
                // Date filtering for count
                if (startDate || endDate) {
                    const surveyDate = parseDate(survey.survey_date);
                    if (surveyDate) {
                        // Normalize dates to ignore time component
                        const normalizedSurveyDate = new Date(surveyDate.getFullYear(), surveyDate.getMonth(), surveyDate.getDate());
                        
                        if (startDate && normalizedSurveyDate < new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate())) {
                            return; // Skip - before start date
                        }
                        if (endDate && normalizedSurveyDate > new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate())) {
                            return; // Skip - after end date
                        }
                    }
                    // If we can't parse the date, we might want to skip or include based on requirements
                    else if (startDate || endDate) {
                        return; // Skip records with unparseable dates
                    }
                }
                
                totalCount++;
                currentFilteredSurveys.push(survey); // Store all matches for list view
            });
            
            if (markerCount === totalCount) {
                updateStatusBar('Loaded ' + markerCount + ' markers (all matching filters)');
            } else {
                updateStatusBar('Loaded ' + markerCount + ' markers (limited display, ' + totalCount + ' total matching filters)');
            }
                        // Uniform zoom handling
                if (bounds.length > 0) {
                    var boundsGroup = L.latLngBounds(bounds);
                    // Use fitBounds with maxZoom to handle outliers safely
                    map.fitBounds(boundsGroup, {padding: [50, 50], maxZoom: 16});
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
            clearDateRange(); // Clear date filters as well
            changeBaseLayer();
            map.setView([32.0833, 72.6667], 11);
            markers.clearLayers();
            currentMarkerCount = 0;
            updateStatusBar('Filters reset. Select and apply to load data.');
        }
        
        // Don't load any markers initially for performance
        updateStatusBar('Ready. Select filters and click Apply.');
        
        // Function to load all markers without limit
        function loadAllMarkers() {
            var originalMaxMarkers = MAX_MARKERS;
            MAX_MARKERS = surveyData.length; // Set to total number of records
            applyFilters();
            MAX_MARKERS = originalMaxMarkers; // Restore original limit
        }
        
        // Function to collapse the panel
        function collapsePanel() {
            var infoPanel = document.getElementById('infoPanel');
            var collapseBtn = document.getElementById('collapseBtn');
            var floatingBtn = document.getElementById('floatingExpandBtn');
            
            // Hide the info panel
            infoPanel.style.display = 'none';
            
            // Show the floating expand button
            floatingBtn.style.display = 'block';
            
            // Update button text (though it won't be visible)
            collapseBtn.textContent = 'Expand Panel';
        }
        
        // Function to expand the panel
        function expandPanel() {
            var infoPanel = document.getElementById('infoPanel');
            var floatingBtn = document.getElementById('floatingExpandBtn');
            
            // Show the info panel
            infoPanel.style.display = 'block';
            
            // Hide the floating expand button
            floatingBtn.style.display = 'none';
        }
        
        // Image Viewer Functions
        var currentImageUrls = [];
        var currentImageIndex = 0;
        var currentRotation = 0;
        var currentScale = 1;
        
        function openImageViewer(imageUrls, startIndex) {
            currentImageUrls = imageUrls;
            currentImageIndex = startIndex || 0;
            currentRotation = 0; // Reset rotation when opening new viewer
            currentScale = 1; // Reset scale when opening new viewer
            
            var modal = document.getElementById('imageModal');
            var modalImg = document.getElementById('modalImage');
            var counter = document.getElementById('imageCounter');
            var thumbnailStrip = document.getElementById('thumbnailStrip');
            
            // Set current image
            modalImg.src = currentImageUrls[currentImageIndex];
            updateImageTransform(modalImg);
            
            // Update counter
            counter.textContent = (currentImageIndex + 1) + ' / ' + currentImageUrls.length;
            
            // Create thumbnails
            thumbnailStrip.innerHTML = '';
            for (var i = 0; i < currentImageUrls.length; i++) {
                var thumb = document.createElement('img');
                thumb.className = 'thumbnail';
                thumb.src = currentImageUrls[i];
                thumb.alt = 'Thumbnail ' + (i + 1);
                thumb.onclick = (function(index) {
                    return function() {
                        showImage(index);
                    };
                })(i);
                
                if (i === currentImageIndex) {
                    thumb.classList.add('active');
                }
                
                thumbnailStrip.appendChild(thumb);
            }
            
            // Show modal
            modal.style.display = 'block';
            
            // Close popup
            map.closePopup();
        }
        
        function closeImageViewer() {
            var modal = document.getElementById('imageModal');
            modal.style.display = 'none';
            currentImageUrls = [];
            currentImageIndex = 0;
            currentRotation = 0;
            currentScale = 1;
        }

        var currentFilteredSurveys = [];
        var listPageSize = 50;
        var listCurrentIndex = 0;
        
        function showListView() {
            var modal = document.getElementById('listModal');
            var sidebar = document.getElementById('explorerSidebar');
            var detail = document.getElementById('explorerDetail');
            
            sidebar.innerHTML = '';
            detail.innerHTML = '<div style="text-align: center; color: #94a3b8; margin-top: 80px;"><div style="font-size: 60px; margin-bottom: 20px;">📋</div><div style="font-size: 18px; font-weight: 600; color: #475569;">Select a Record</div><div style="font-size: 14px; margin-top: 8px;">Pick a survey from the sidebar to view full details and gallery</div></div>';
            listCurrentIndex = 0;
            
            var titleText = document.getElementById('listTitleText');
            var searchBadge = document.getElementById('searchCount');
            
            titleText.textContent = 'Filtered Records';
            searchBadge.textContent = currentFilteredSurveys.length;
            
            // Show active filters in main header
            var district = document.getElementById('districtFilter').value;
            var tehsil = document.getElementById('tehsilFilter').value;
            var mcuc = document.getElementById('mcucFilter').value;
            var filterInfo = document.getElementById('activeFilterInfo');
            filterInfo.innerHTML = 'Filters: <span style="color:#1a202c">' + district + '</span> > <span style="color:#1a202c">' + tehsil + '</span> > <span style="color:#1a202c">' + mcuc + '</span>';
            
            // Clear search input
            document.getElementById('listSearch').value = '';
            
            renderListBatch();
            
            // Auto-select first item if exists
            if (currentFilteredSurveys.length > 0) {
                selectExplorerSurvey(currentFilteredSurveys[0]);
            }
            
            modal.style.display = 'block';
        }

        function renderListBatch() {
            var sidebar = document.getElementById('explorerSidebar');
            var batch = currentFilteredSurveys.slice(listCurrentIndex, listCurrentIndex + listPageSize);
            
            if (listCurrentIndex === 0) {
                if (batch.length === 0) {
                    sidebar.innerHTML = '<div style="text-align: center; padding: 40px; color: #7f8c8d;">No records found.</div>';
                    return;
                }
                sidebar.innerHTML = '<table><thead><tr><th>ID</th><th style="text-align: right;">Type</th></tr></thead><tbody id="explorerTableBody"></tbody></table>';
            }
            
            var tableBody = document.getElementById('explorerTableBody');

            // Remove previous "Load More" button row if it exists
            var oldBtnRow = document.getElementById('loadMoreRow');
            if (oldBtnRow) oldBtnRow.remove();

            batch.forEach(function(survey) {
                var row = document.createElement('tr');
                row.className = 'list-row';
                row.id = 'row-' + survey.survey_id;
                row.onclick = function() { selectExplorerSurvey(survey); };
                
                var typeLabel = survey.consumer_type.substring(0,3).toUpperCase();
                var typeColor = survey.consumer_type === 'Domestic' ? '#27ae60' : '#d35400';
                
                row.innerHTML = 
                    '<td><span class="row-id">' + survey.survey_id + '</span></td>' +
                    '<td class="sidebar-type" style="text-align: right;"><span style="font-size: 10px; color: ' + typeColor + '; font-weight: bold;">' + typeLabel + '</span></td>';
                
                tableBody.appendChild(row);
            });

            listCurrentIndex += listPageSize;

            if (listCurrentIndex < currentFilteredSurveys.length) {
                var loadMoreRow = document.createElement('tr');
                loadMoreRow.id = 'loadMoreRow';
                loadMoreRow.innerHTML = '<td colspan="3" style="text-align: center; padding: 15px;"><button onclick="renderListBatch()" style="background: transparent; color: #3498db; border: 1px solid #3498db; padding: 5px 20px; border-radius: 15px; cursor: pointer; font-size: 11px;">Load More</button></td>';
                tableBody.appendChild(loadMoreRow);
            }
        }
        
        function selectExplorerSurvey(survey) {
            // Update UI selection
            var rows = document.getElementsByClassName('list-row');
            for (var i = 0; i < rows.length; i++) {
                rows[i].classList.remove('active');
            }
            var activeRow = document.getElementById('row-' + survey.survey_id);
            if (activeRow) activeRow.classList.add('active');
            
            // Populate Detail Pane
            var detail = document.getElementById('explorerDetail');
            var imageUrls = survey.image_urls || [];
            
            // Build Info Grid with highlights
            var infoGridHtml = '<div class="detail-info-grid">';
            
            // 1. Date and Time (Top Full Width)
            infoGridHtml += 
                '<div class="info-item" style="grid-column: span 2; border-bottom: 1px dashed #edf2f7; padding-bottom: 10px; margin-bottom: 5px;">' +
                    '<div class="info-label" style="font-size: 10px; color: #718096;">Submission Timestamp</div>' +
                    '<div class="info-value" style="color: #4a5568; font-size: 13px; font-weight: 600;">' + (survey.survey_date || 'N/A') + ' ' + (survey.survey_time || '') + '</div>' +
                '</div>';

            // 2. ID and Surveyor Name side-by-side
            infoGridHtml += 
                '<div class="info-item" style="background: #f8fafc; padding: 10px; border-radius: 10px; border: 1px solid #e2e8f0;">' +
                    '<div class="info-label" style="color: #3182ce; font-size: 10px;">Survey ID</div>' +
                    '<div class="info-value" style="color: #1a202c; font-size: 15px; font-weight: 800;">#' + survey.survey_id + '</div>' +
                '</div>' +
                '<div class="info-item" style="background: #f8fafc; padding: 10px; border-radius: 10px; border: 1px solid #e2e8f0;">' +
                    '<div class="info-label" style="color: #3182ce; font-size: 10px;">Surveyor Personnel</div>' +
                    '<div class="info-value" style="color: #1a202c; font-size: 15px; font-weight: 800;">' + (survey.surveyor_name || 'N/A') + '</div>' +
                '</div>';

            // 3. Consumer Name (Full width)
            infoGridHtml += 
                '<div class="info-item" style="grid-column: span 2; margin-top: 5px;">' +
                    '<div class="info-label">Consumer Name</div>' +
                    '<div class="info-value" style="color: #1a202c; font-weight: 700; font-size: 16px;">' + (survey.consumer_name || 'N/A') + '</div>' +
                '</div>';

            // 4. Site Address (Full width)
            infoGridHtml += 
                '<div class="info-item" style="grid-column: span 2; margin-bottom: 5px;">' +
                    '<div class="info-label">Site Address</div>' +
                    '<div class="info-value" style="line-height: 1.4; color: #4a5568; font-size: 13px;">' + (survey.consumer_address || 'N/A') + '</div>' +
                '</div>';

            // Update unified map button
            var mapBtn = document.getElementById('detailMapBtn');
            mapBtn.style.display = 'flex';
            mapBtn.onclick = function() { zoomToMarker(survey); };

            var infoFields = [
                { label: 'Category Type', value: survey.consumer_type + (survey.uc_type ? ' (' + survey.uc_type + ')' : ''), highlight: false },
                { label: 'Level', value: survey.level || 'N/A', highlight: false },
                { label: 'Type', value: survey.survey_type || 'N/A', highlight: false },
                { label: 'Structure Type', value: survey.house_type || 'N/A', highlight: false },
                { label: 'Administrative Unit', value: survey.mc_uc, highlight: false }
            ];
            
            infoFields.forEach(function(field, idx) {
                infoGridHtml += 
                    '<div class="info-item">' +
                        '<div class="info-label">' + field.label + '</div>' +
                        '<div class="info-value" style="font-size: 13px;">' + field.value + '</div>' +
                    '</div>';
            });
            infoGridHtml += '</div>';
            
            var galleryHtml = '';
            if (imageUrls.length > 0) {
                galleryHtml = '<div style="margin-bottom: 12px; font-size: 11px; color: #718096; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">Field Media Gallery (' + imageUrls.length + ')</div>' +
                              '<div class="explorer-gallery">';
                imageUrls.forEach(function(url, idx) {
                    galleryHtml += '<img src="' + url + '" class="explorer-thumb" onclick="openImageViewer(' + JSON.stringify(imageUrls).replace(/"/g, '&quot;') + ', ' + idx + ')" alt="Survey Image">';
                });
                galleryHtml += '</div>';
            } else {
                galleryHtml = '<div style="text-align: center; padding: 50px 20px; background: #fff; border-radius: 16px; color: #94a3b8; border: 2px dashed #e2e8f0; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">' +
                              '<div style="font-size: 40px; margin-bottom: 10px;">🖼️</div>' +
                              'No images attached to this record</div>';
            }

            detail.innerHTML = 
                '<div class="detail-split-content">' +
                    '<div class="detail-gallery-column">' + galleryHtml + '</div>' + 
                    '<div class="detail-info-column">' + infoGridHtml + '</div>' + 
                '</div>';
        }
        
        function closeListView() {
            document.getElementById('listModal').style.display = 'none';
            document.getElementById('detailMapBtn').style.display = 'none';
        }

        function filterList() {
            var search = document.getElementById('listSearch').value.toLowerCase();
            var sidebar = document.getElementById('explorerSidebar');
            
            // If search is empty, go back to paginated view
            if (search.length === 0) {
                sidebar.innerHTML = '';
                listCurrentIndex = 0;
                renderListBatch();
                return;
            }

            // Search the entire array
            var matched = currentFilteredSurveys.filter(function(survey) {
                var content = (survey.survey_id + ' ' + survey.mc_uc + ' ' + (survey.surveyor_name || '')).toLowerCase();
                return content.indexOf(search) > -1;
            });

            // Render search results
            sidebar.innerHTML = '<table><thead><tr><th>ID</th><th style="text-align: right;">Type</th></tr></thead><tbody id="explorerTableBody"></tbody></table>';
            var tableBody = document.getElementById('explorerTableBody');
            
            var resultsToDisplay = matched.slice(0, 100);
            document.getElementById('searchCount').textContent = matched.length;
            
            if (resultsToDisplay.length === 0) {
                sidebar.innerHTML = '<div style="text-align: center; padding: 40px; color: #7f8c8d;">No results matching "' + search + '"</div>';
            } else {
                resultsToDisplay.forEach(function(survey) {
                    var row = document.createElement('tr');
                    row.className = 'list-row';
                    row.id = 'row-' + survey.survey_id;
                    row.onclick = function() { selectExplorerSurvey(survey); };
                    
                    var typeLabel = survey.consumer_type.substring(0,3).toUpperCase();
                    var typeColor = survey.consumer_type === 'Domestic' ? '#27ae60' : '#d35400';
                    
                    row.innerHTML = 
                        '<td><span class="row-id">' + survey.survey_id + '</span></td>' +
                        '<td class="sidebar-type" style="text-align: right;"><span style="font-size: 10px; color: ' + typeColor + '; font-weight: bold;">' + typeLabel + '</span></td>';
                    
                    tableBody.appendChild(row);
                });
            }
        }
        
        function zoomToMarker(survey) {
            closeListView();
            var coords = survey.location.split(',');
            var lat = parseFloat(coords[0]);
            var lng = parseFloat(coords[1]);
            
            map.setView([lat, lng], 18);
            
            // Find and open popup
            markers.eachLayer(function(layer) {
                var latlng = layer.getLatLng();
                if (latlng.lat === lat && latlng.lng === lng) {
                    layer.openPopup();
                }
            });
        }
        
        function changeImage(direction) {
            showImage(currentImageIndex + direction);
        }
        
        function showImage(index) {
            if (currentImageUrls.length === 0) return;
            
            // Normalize index
            if (index >= currentImageUrls.length) {
                currentImageIndex = 0;
            } else if (index < 0) {
                currentImageIndex = currentImageUrls.length - 1;
            } else {
                currentImageIndex = index;
            }
            
            var modalImg = document.getElementById('modalImage');
            var counter = document.getElementById('imageCounter');
            var thumbnails = document.querySelectorAll('.thumbnail');
            
            // Update image
            modalImg.src = currentImageUrls[currentImageIndex];
            
            // Reset transform for new image
            currentRotation = 0;
            currentScale = 1;
            // Reset translate values by setting transform directly
            if (modalImg) {
                modalImg.style.transform = 'rotate(0deg) scale(1) translate(0px, 0px)';
            }
            
            // Update counter
            counter.textContent = (currentImageIndex + 1) + ' / ' + currentImageUrls.length;
            
            // Update active thumbnail
            for (var i = 0; i < thumbnails.length; i++) {
                thumbnails[i].classList.remove('active');
                if (i === currentImageIndex) {
                    thumbnails[i].classList.add('active');
                }
            }
        }
        
        // Image Transform Functions
        function updateImageTransform(imgElement) {
            if (!imgElement) return;
            
            // Get current translate values if they exist
            var currentTransform = imgElement.style.transform || '';
            var translateMatch = currentTransform.match(/translate\\(([^)]+)\\)/);
            var translateX = 0, translateY = 0;
            
            if (translateMatch) {
                var translateValues = translateMatch[1].split(',');
                translateX = parseFloat(translateValues[0]) || 0;
                translateY = parseFloat(translateValues[1]) || 0;
            }
            
            imgElement.style.transform = 'rotate(' + currentRotation + 'deg) scale(' + currentScale + ') translate(' + translateX + 'px, ' + translateY + 'px)';
        }
        
        function rotateImage(degrees) {
            var modalImg = document.getElementById('modalImage');
            if (!modalImg) return;
            
            currentRotation = (currentRotation + degrees) % 360;
            updateImageTransform(modalImg);
        }
        
        function zoomImage(factor) {
            var modalImg = document.getElementById('modalImage');
            if (!modalImg) return;
            
            // Limit zoom between 0.5x and 5x
            var newScale = currentScale * factor;
            if (newScale >= 0.5 && newScale <= 5) {
                currentScale = newScale;
                updateImageTransform(modalImg);
                
                // Update cursor based on zoom level
                modalImg.style.cursor = newScale > 1 ? 'grab' : 'default';
            }
        }
        
        function resetImageTransform() {
            var modalImg = document.getElementById('modalImage');
            if (!modalImg) return;
            
            currentRotation = 0;
            currentScale = 1;
            // Reset translate values by setting transform directly
            modalImg.style.transform = 'rotate(0deg) scale(1) translate(0px, 0px)';
        }
        
        // Improved touch gesture support for mobile zoom and swipe navigation
        var touchStartDistance = 0;
        var touchStartX = 0;
        var isSwiping = false;
        
        function getTouchDistance(e) {
            if (e.touches.length < 2) return 0;
            var dx = e.touches[0].clientX - e.touches[1].clientX;
            var dy = e.touches[0].clientY - e.touches[1].clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }
        
        // Add touch event listeners to the entire modal for better reliability
        var modalElement = document.getElementById('imageModal');
        var modalImage = document.getElementById('modalImage');
        
        modalImage.addEventListener('touchstart', function(e) {
            if (e.touches.length === 2) {
                e.preventDefault();
                touchStartDistance = getTouchDistance(e);
                isSwiping = false;
            } else if (e.touches.length === 1) {
                touchStartX = e.touches[0].clientX;
                isSwiping = true;
            }
        }, { passive: false });
        
        modalImage.addEventListener('touchmove', function(e) {
            if (e.touches.length === 2 && touchStartDistance > 0) {
                e.preventDefault();
                var currentDistance = getTouchDistance(e);
                var scaleChange = currentDistance / touchStartDistance;
                
                // Limit zoom between 0.5x and 5x
                var newScale = currentScale * scaleChange;
                if (newScale >= 0.5 && newScale <= 5) {
                    currentScale = newScale;
                    updateImageTransform(document.getElementById('modalImage'));
                }
            } else if (e.touches.length === 1 && isSwiping) {
                // Handle swipe navigation
                var touchX = e.touches[0].clientX;
                var deltaX = touchX - touchStartX;
                
                // Only navigate if swiped a significant distance
                if (Math.abs(deltaX) > 50) {
                    if (deltaX > 0) {
                        // Swiped right - previous image
                        changeImage(-1);
                    } else {
                        // Swiped left - next image
                        changeImage(1);
                    }
                    isSwiping = false; // Prevent multiple navigations
                }
            }
        });
        
        modalImage.addEventListener('touchend', function(e) {
            touchStartDistance = 0;
            isSwiping = false;
        });
        
        // Enable mouse wheel zooming and panning on desktop
        var isDragging = false;
        var lastX, lastY;
        
        modalImage.addEventListener('wheel', function(e) {
            e.preventDefault();
            var delta = e.deltaY;
            var factor = delta < 0 ? 1.1 : 0.9;
            zoomImage(factor);
        });
        
        modalImage.addEventListener('mousedown', function(e) {
            e.preventDefault();
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
            modalImage.style.cursor = 'grabbing';
        });
        
        modalImage.addEventListener('mousemove', function(e) {
            if (isDragging && currentScale > 1) {
                e.preventDefault();
                var deltaX = e.clientX - lastX;
                var deltaY = e.clientY - lastY;
                
                // Apply panning transformation
                var modalImg = document.getElementById('modalImage');
                var currentTransform = modalImg.style.transform || '';
                
                // Extract current translate values if they exist
                var translateMatch = currentTransform.match(/translate\\(([^)]+)\\)/);
                var translateX = 0, translateY = 0;
                
                if (translateMatch) {
                    var translateValues = translateMatch[1].split(',');
                    translateX = parseFloat(translateValues[0]) || 0;
                    translateY = parseFloat(translateValues[1]) || 0;
                }
                
                // Update translate values
                translateX += deltaX;
                translateY += deltaY;
                
                // Apply updated transform
                var rotationPart = currentTransform.replace(/translate\\([^)]*\\)/g, '');
                modalImg.style.transform = rotationPart + ' translate(' + translateX + 'px, ' + translateY + 'px)';
                
                // Update last positions
                lastX = e.clientX;
                lastY = e.clientY;
            }
        });
        
        modalImage.addEventListener('mouseup', function(e) {
            isDragging = false;
            modalImage.style.cursor = 'grab';
        });
        
        modalImage.addEventListener('mouseleave', function(e) {
            isDragging = false;
            modalImage.style.cursor = 'default';
        });
        
        // Handle browser back button to close image viewer
        window.addEventListener('popstate', function(event) {
            if (document.getElementById('imageModal').style.display === 'block') {
                closeImageViewer();
                // Prevent default back behavior if we just closed the viewer
                if (event.state && event.state.galleryOpen) {
                    event.preventDefault();
                    history.go(1); // Go forward to counteract the back
                }
            }
        });
        
        // Surveyor Stats Functions
        function showSurveyorStats() {
            var modal = document.getElementById('statsModal');
            var container = document.getElementById('statsContent');
            
            if (currentFilteredSurveys.length === 0) {
                alert("No data found for current filters. Please apply filters first.");
                return;
            }

            // Aggregate data
            var stats = {};
            currentFilteredSurveys.forEach(function(survey) {
                var name = survey.surveyor_name || "Unknown Surveyor";
                if (!stats[name]) {
                    stats[name] = { total: 0, domestic: 0, commercial: 0 };
                }
                stats[name].total++;
                if (survey.consumer_type === 'Domestic') stats[name].domestic++;
                if (survey.consumer_type === 'Commercial') stats[name].commercial++;
            });

            // Sort surveyors by total count descending
            var sortedNames = Object.keys(stats).sort(function(a, b) {
                return stats[b].total - stats[a].total;
            });

            // Generate Table
            var html = '<table class="stats-table">' +
                       '<thead><tr>' +
                       '<th>#</th><th>Surveyor Name</th><th>Domestic</th><th>Commercial</th><th>Total Submissions</th>' +
                       '</tr></thead><tbody>';

            sortedNames.forEach(function(name, index) {
                var s = stats[name];
                html += '<tr>' +
                        '<td><span class="rank-badge">' + (index + 1) + '</span></td>' +
                        '<td style="font-weight:bold; color:#2c3e50;">' + name + '</td>' +
                        '<td style="color:#27ae60;">' + s.domestic + '</td>' +
                        '<td style="color:#e67e22;">' + s.commercial + '</td>' +
                        '<td style="font-weight:bold;">' + s.total + '</td>' +
                        '</tr>';
            });

            html += '</tbody></table>';
            
            // Add a grand total footer
            html += '<div style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:8px; border-left:4px solid #9b59b6;">' +
                    '<strong>Total Records in Selection:</strong> ' + currentFilteredSurveys.length + '</div>';

            container.innerHTML = html;
            modal.style.display = 'block';
        }

        function closeStatsView() {
            document.getElementById('statsModal').style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            var modal = document.getElementById('imageModal');
            if (event.target === modal) {
                closeImageViewer();
            }
        }
        
        // Keyboard navigation
        document.onkeydown = function(e) {
            if (document.getElementById('imageModal').style.display === 'block') {
                switch(e.keyCode) {
                    case 27: // ESC
                        closeImageViewer();
                        break;
                    case 37: // Left arrow
                        changeImage(-1);
                        break;
                    case 39: // Right arrow
                        changeImage(1);
                        break;
                    case 107: // Plus key
                    case 187: // Plus key (Firefox)
                        zoomImage(1.2);
                        break;
                    case 109: // Minus key
                    case 189: // Minus key (Firefox)
                        zoomImage(0.8);
                        break;
                }
            }
        }
        
        // Initialize with panel expanded as per project configuration
        document.addEventListener('DOMContentLoaded', function() {
            var infoPanel = document.getElementById('infoPanel');
            var floatingBtn = document.getElementById('floatingExpandBtn');
            
            // Show the info panel
            infoPanel.style.display = 'block';
            
            // Hide the floating expand button
            floatingBtn.style.display = 'none';
            
            // Initialize filters - default to Sargodha district, Sargodha tehsil, and MC-1
            document.getElementById('districtFilter').value = 'Sargodha';
            populateTehsilFilter();
            // Set tehsil to Sargodha
            document.getElementById('tehsilFilter').value = 'Sargodha';
            populateMCUCFilter();
            // Set MC/UC to MC-1 (first option that contains 'MC-1')
            var mcucSelect = document.getElementById('mcucFilter');
            for (var i = 0; i < mcucSelect.options.length; i++) {
                if (mcucSelect.options[i].text.includes('MC-1') || mcucSelect.options[i].value.includes('MC-1')) {
                    mcucSelect.selectedIndex = i;
                    break;
                }
            }
            // Apply filters to show initial data
            applyFilters();
        });
    </script></body>
</html>'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated final fixed map file: {output_file}")

def process_csv_files():
    """Process CSV files and generate map data"""
    csv_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.csv') and 'SURVEY_DATA' in f]
    
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
    print("  Final Fixed Field Staff Map Generator")
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
    print("  - Date filtering capability")
    print("  - Surveyor name in tooltips")
    print("  - Creator credits: Kashif Khalil")
    print("  - Fixed button visibility issues")
    print("==============================================")

if __name__ == "__main__":
    main()