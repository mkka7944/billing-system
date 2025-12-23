#!/usr/bin/env python3
"""
Modern Mobile-First Field Staff Map Generator
Optimized for performance and mobile experience.
"""

import pandas as pd
import os
import json
import re
from collections import defaultdict
import datetime

# Configuration
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), "..", "outputs", "scraped_data")
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))

class ModernMapGenerator:
    def __init__(self):
        self.data_by_location = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.seen_survey_ids = set()
        self.duplicates_count = 0
        self.total_records = 0
        
    def get_marker_color(self, identifier):
        """Generate consistent robust colors"""
        hash_val = hash(identifier) % 360
        hue_spread = (hash_val * 137.508) % 360
        saturation = 75 + (hash_val % 25)
        lightness = 45 + (hash_val % 15)
        return f"hsl({hue_spread}, {saturation}%, {lightness}%)"

    def shorten_name(self, name, district, tehsil):
        """Smart name shortener"""
        original = name
        name = name.replace(f"{district} - ", "").replace(f"{tehsil} - ", "")
        
        # Match patterns like MC-1, UC-4
        match = re.search(r'((?:MC|UC|Zone|Ward)[-\s]*\d+)', name, re.IGNORECASE)
        if match:
            return match.group(1).upper().replace(' ', '')
        
        # Fallback to first word or comma split
        return name.split(',')[0].strip().split()[0]

    def process_csvs(self):
        """Read and process records with deduplication"""
        if not os.path.exists(INPUT_FOLDER):
            print(f"Input folder not found: {INPUT_FOLDER}")
            return False

        csv_files = [f for f in os.listdir(INPUT_FOLDER) 
                     if f.endswith('.csv') 
                     and 'SURVEY' in f.upper() 
                     and 'MASTER' not in f.upper()
                     and 'PAID_ALL_HISTORY' not in f.upper()]
        
        if not csv_files:
            print("No suitable CSV files found.")
            return False

        print(f"Processing {len(csv_files)} files...")
        
        for csv_file in csv_files:
            file_path = os.path.join(INPUT_FOLDER, csv_file)
            print(f"  - {csv_file}")
            
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
                
                # Validation
                req_cols = ['Latitude', 'Longitude', 'District', 'Tehsil', 'Union Council']
                if not all(col in df.columns for col in req_cols):
                    print(f"    Skipping: Missing columns")
                    continue
                
                for _, row in df.iterrows():
                    # Dedup logic
                    sid = str(row.get('Survey ID', '')).strip()
                    if sid and sid in self.seen_survey_ids:
                        self.duplicates_count += 1
                        continue
                    if sid:
                        self.seen_survey_ids.add(sid)
                    
                    # Location check
                    lat = str(row.get('Latitude', '')).strip()
                    lon = str(row.get('Longitude', '')).strip()
                    if not lat or not lon:
                        continue
                    
                    # Extract Data
                    district = str(row.get('District', '')).strip().upper()
                    tehsil = str(row.get('Tehsil', '')).strip().upper()
                    uc = str(row.get('Union Council', '')).strip()
                    mc_uc_name = f"{district} - {uc}" if uc else f"{district} - {tehsil}"
                    
                    # Collect Images
                    images = []
                    for i in range(1, 5):
                        url = str(row.get(f'Image URL {i}', '')).strip()
                        if url and url.lower() != 'nan':
                            images.append(url)
                            
                    record = {
                        'id': sid,
                        'lat': float(lat),
                        'lng': float(lon),
                        'd': district,
                        't': tehsil,
                        'mu': mc_uc_name,
                        'type': str(row.get('Consumer Type', '')).strip(),
                        'name': str(row.get('Name', '')).strip(),
                        'addr': str(row.get('Address', '')).strip(),
                        'house': str(row.get('House Type', '')).strip(),
                        's_name': str(row.get('Surveyor Name', '')).strip(),
                        'date': str(row.get('Survey Date', '')).strip(),
                        'time': str(row.get('Survey Time', '')).strip(),
                        'imgs': images
                    }
                    
                    self.data_by_location[district][tehsil][mc_uc_name].append(record)
                    self.total_records += 1
                    
            except Exception as e:
                print(f"    Error: {e}")
        
        return True


    def generate_optimized_json(self):
        """
        Convert complex dict structure to flat array for client-side processing.
        """
        flat_records = []
        hierarchy = {} 
        
        print("Optimizing data structure...")
        
        for district, tehsils in self.data_by_location.items():
            hierarchy[district] = {}
            for tehsil, mcucs in tehsils.items():
                hierarchy[district][tehsil] = {}
                for mcuc_name, records in mcucs.items():
                    color = self.get_marker_color(mcuc_name)
                    short = self.shorten_name(mcuc_name, district, tehsil)
                    
                    hierarchy[district][tehsil][mcuc_name] = {
                        'c': color,
                        's': short,
                        'cnt': len(records)
                    }
                    
                    for r in records:
                        is_com = 1 if r['type'].lower() == 'commercial' else 0
                        flat_records.append([
                            r['id'],           # 0
                            r['lat'],          # 1
                            r['lng'],          # 2
                            is_com,            # 3
                            r['name'],         # 4
                            r['addr'],         # 5
                            r['s_name'],       # 6
                            r['date'],         # 7
                            r['time'],         # 8
                            r['imgs'],         # 9
                            district,          # 10
                            tehsil,            # 11
                            mcuc_name,         # 12
                            r['house']         # 13
                        ])
                        
        return flat_records, hierarchy

    def generate_html(self, output_file="modern_map.html"):
        records, hierarchy = self.generate_optimized_json()
        
        json_records = json.dumps(records).replace('`', '\\`').replace('${', '\\${')
        json_hierarchy = json.dumps(hierarchy).replace('`', '\\`').replace('${', '\\${')
        
        
        # Sorting code with proper regex (using raw string to avoid escaping issues)
        sorting_code = r"""
                // Extract numbers using regex
                const aMatch = aShort.match(/\d+/);
                const bMatch = bShort.match(/\d+/);
                const aNum = aMatch ? parseInt(aMatch[0]) : 0;
                const bNum = bMatch ? parseInt(bMatch[0]) : 0;
        """
        
        # Embedded Data Scripts
        embedded_data = f"""
        <script>
            const RAW_DATA = {json_records};
            const HIERARCHY = {json_hierarchy};
        </script>
        """

        css_style = """
        :root { 
            --primary: #2563eb; --warning: #f59e0b; --danger: #ef4444; --text: #1e293b; --bg: #f8fafc; --sidebar-w: 350px; 
            --font-xs: 11px; --font-sm: 13px; --font-base: 14px; --font-md: 16px; --font-lg: 18px;
        }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { margin: 0; padding: 0; font-family: 'Inter', sans-serif; height: 100vh; display: flex; overflow: hidden; background: var(--bg); font-size: var(--font-base); color: var(--text); }
        
        /* Layout */
        #sidebar { 
            width: var(--sidebar-w); background: white; border-right: 1px solid #e2e8f0; 
            display: flex; flex-direction: column; z-index: 2000; box-shadow: 0 0 40px rgba(0,0,0,0.03);
            transition: transform 0.3s ease;
        }
        #main-stage { flex: 1; position: relative; display: flex; flex-direction: column; overflow: hidden; }
        #map-container { flex: 1; position: relative; }
        #map { width: 100%; height: 100%; }

        /* Fullscreen List View */
        #list-view-stage { 
            position: absolute; inset: 0; background: var(--bg); z-index: 5000; 
            display: none; flex-direction: column; overflow: hidden; 
        }
        #list-view-stage.active { display: flex; }
        
        .list-nav { 
            display: flex; justify-content: space-between; align-items: center; 
            padding: 16px; background: white; border-bottom: 1px solid #e2e8f0;
        }

        .record-card {
            flex: 1; display: flex; flex-direction: column; padding: 24px;
            max-width: 600px; margin: 0 auto; width: 100%; overflow-y: auto;
        }
        .card-header { margin-bottom: 24px; border-bottom: 2px solid #f1f5f9; padding-bottom: 16px; }
        .card-title { font-size: var(--font-lg); font-weight: 700; color: var(--text); }
        .card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .grid-item { display: flex; flex-direction: column; gap: 6px; }
        .grid-label { font-size: var(--font-xs); font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
        .grid-val { font-size: var(--font-base); font-weight: 500; color: var(--text); }

        .card-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
        .gallery-thumb { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 12px; cursor: pointer; border: 2px solid transparent; transition: all 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .gallery-thumb:hover { border-color: var(--primary); transform: translateY(-2px); }

        /* Sidebar UI refinements */
        .filters { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
        .filter-group { display: flex; flex-direction: column; gap: 8px; }
        .filter-label { font-size: var(--font-xs); font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }
        
        /* Modernized Multi-Select List */
        .multi-select-container { 
            border: 1px solid #e2e8f0; border-radius: 10px; background: #fdfdfd; 
            max-height: 180px; overflow-y: auto; padding: 6px; display: flex; flex-direction: column; gap: 4px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }
        .multi-option { 
            display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 8px; 
            font-size: var(--font-sm); color: var(--text); cursor: pointer; transition: all 0.15s ease;
            user-select: none; border: 1px solid transparent;
        }
        .multi-option:hover { background: #f8fafc; border-color: #f1f5f9; }
        .multi-option input { 
            width: 18px; height: 18px; border-radius: 5px; border: 2px solid #cbd5e1; 
            accent-color: var(--primary); margin: 0; cursor: pointer;
        }
        .multi-option.selected { background: #eff6ff; color: var(--primary); font-weight: 600; border-color: #dbeafe; }
        .multi-option span { flex: 1; pointer-events: none; }
        
        .filter-header { 
            display: flex; justify-content: space-between; align-items: flex-end; padding: 0 4px;
        }
        .filter-actions { display: flex; gap: 8px; }
        .select-all-btn { 
            font-size: 10px; font-weight: 800; color: var(--primary); cursor: pointer; 
            text-transform: uppercase; background: none; border: none; padding: 0;
            transition: color 0.2s;
        }
        .select-all-btn:hover { color: #1e40af; text-decoration: underline; }
        .select-all-btn.unselect { color: #64748b; }

        .apply-btn { 
            padding: 14px; background: var(--primary); color: white; border: none; 
            border-radius: 12px; font-weight: 700; cursor: pointer; display: flex; align-items: center; 
            justify-content: center; gap: 10px; font-size: var(--font-base);
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3); transition: all 0.2s;
        }
        .apply-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
        .apply-btn:active { transform: translateY(0); }
        
        .secondary-btn {
            width:100%; padding:12px; border-radius:10px; border:1px solid #e2e8f0; 
            background:white; font-weight:600; font-size: 13px; display:flex; align-items:center; gap:8px;
            transition: all 0.2s; margin-bottom: 8px;
        }
        .secondary-btn:hover { background: #f8fafc; border-color: #cbd5e1; }
        .secondary-btn span { font-size: 20px; }

        .stat-badge {
            background: #eff6ff; color: #1e40af; padding: 8px 16px; border-radius: 12px;
            display: flex; justify-content: space-between; align-items: center;
            border: 1px solid #dbeafe; margin: 12px 16px; box-shadow: 0 2px 4px rgba(30, 64, 175, 0.05);
        }
        .stat-badge span { font-size: 20px; font-weight: 800; }
        .stat-badge small { font-size: 11px; text-transform: uppercase; font-weight: 700; opacity: 0.9; letter-spacing: 0.3px; }

        .guide-box {
            background: #fafafa; border: 1px solid #f1f5f9; border-radius: 12px;
            padding: 16px; margin: 0 24px 20px; color: #475569; font-size: 13px;
            text-align: center;
        }
        .guide-box-content { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; align-items: center; }
        .guide-item { 
            display: flex; align-items: center; gap: 8px; white-space: nowrap; 
            background: #fff; padding: 6px 14px; border-radius: 20px; border: 1px solid #e2e8f0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .guide-item i { font-size: 16px; }
        .guide-item b { color: #1e293b; font-weight: 700; }
        .guide-item span.penalty { 
            background: #fee2e2; color: #b91c1c; font-size: 10px; padding: 2px 6px; 
            border-radius: 6px; font-weight: 800; margin-left: 4px;
        }
        .guide-box h4 { color: #1e293b; font-size: 14px; margin: 0 0 12px 0; font-weight: 700; }
        .fail-mark { color: #ef4444; font-size: 16px; margin-left: 2px; vertical-align: middle; }
        .pass-mark { color: #22c55e; font-size: 16px; margin-left: 2px; vertical-align: middle; }
        .score-box { display: flex; align-items: center; justify-content: center; gap: 4px; }

        button { cursor: pointer; font-family: inherit; }

        /* Leaderboard */
        .rank-row { border-bottom: 1px solid #f1f5f9; transition: background 0.1s; font-size: 15px; }
        .rank-row:hover { background: #f8fafc; }
        .trophy { margin-left: 6px; display: inline-block; vertical-align: middle; }
        .trophy.gold { font-size: 28px; filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.4)); }
        .trophy.silver { font-size: 20px; filter: drop-shadow(0 0 3px rgba(148, 163, 184, 0.3)); }
        .trophy.bronze { font-size: 18px; filter: drop-shadow(0 0 3px rgba(180, 83, 9, 0.2)); }
        
        .idle-warn { color: var(--warning); font-weight: 700; }
        .idle-danger { color: var(--danger); font-weight: 700; }
        .time-warning { color: var(--danger); font-weight: 800; animation: blink 2s infinite; }
        @keyframes blink { 50% { opacity: 0.6; } }

        .stats-table-container { width: 100%; overflow-x: auto; }
        .count-badge { 
            padding: 6px 14px; border-radius: 24px; font-weight: 800; font-size: 14px;
            background: #f1f5f9; color: #475569; display: inline-block; min-width: 50px; text-align: center;
        }
        .count-high { background: #dcfce7; color: #166534; box-shadow: 0 0 10px rgba(22, 101, 52, 0.1); }
        .status-msg { font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 2px 6px; border-radius: 4px; }
        .status-idle { background: #fee2e2; color: #991b1b; }
        .status-warn { background: #fef3c7; color: #92400e; }
        .status-ok { background: #f0fdf4; color: #166534; }

        /* Modern Tooltip */
        .leaflet-popup-content-wrapper { border-radius: 12px; padding: 0; overflow: hidden; }
        .leaflet-popup-content { margin: 0; width: 220px !important; }
        .pop-card { padding: 12px; }
        .pop-title { font-weight: 700; font-size: 14px; margin-bottom: 4px; color: var(--primary); }

        /* Advanced Gallery */
        .gallery-overlay { 
            display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 10000; 
            flex-direction: column; transition: opacity 0.3s;
        }
        .gallery-overlay.active { display: flex; }
        .gal-header { padding: 16px; display: flex; justify-content: flex-end; color: white; }
        .gal-viewport { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; touch-action: none; }
        .gal-img { max-width: 90%; max-height: 80%; object-fit: contain; transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        
        .gal-controls { 
            padding: 20px; display: flex; justify-content: center; gap: 15px; 
            background: linear-gradient(transparent, rgba(0,0,0,0.5));
        }
        .gal-btn { 
            width: 50px; height: 50px; border-radius: 50%; background: rgba(255,255,255,0.1); 
            border: 1px solid rgba(255,255,255,0.2); color: white; display: flex; 
            align-items: center; justify-content: center; backdrop-filter: blur(8px); cursor: pointer;
        }

        /* Floating Controls */
        .map-controls { 
            position: absolute; bottom: 24px; right: 24px; z-index: 1000; 
            display: flex; flex-direction: column; gap: 12px; align-items: flex-end;
        }
        .control-group { 
            display: flex; flex-direction: column; gap: 8px; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
            opacity: 1; transform: translateY(0);
        }
        .control-group.collapsed { 
            height: 0; opacity: 0; transform: translateY(10px); pointer-events: none; margin-bottom: -12px;
        }
        .float-btn { 
            width: 48px; height: 48px; border-radius: 50%; background: white; 
            color: var(--text); border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            transition: all 0.2s; z-index: 1001;
        }
        .float-btn:hover { background: #f1f5f9; transform: scale(1.05); }
        .float-btn:active { transform: scale(0.95); }
        .float-btn.primary { background: var(--primary); color: white; }
        .float-btn .material-icons-round { font-size: 24px; }

        @media (max-width: 768px) {
            #sidebar { position: fixed; left: -100%; top: 0; bottom: 0; width: 100%; max-width: 320px; }
            #sidebar.open { left: 0; }
            .mobile-only { display: block; }
            .map-controls { bottom: 90px; right: 20px; }
            
            .modal-header { flex-direction: column; align-items: stretch !important; gap: 16px; padding: 16px !important; }
            .modal-header > div { width: 100%; justify-content: space-between; }
            .perf-table th, .perf-table td { padding: 10px 4px !important; font-size: 12px; }
            .modal-header input[type="date"] { font-size: 13px; max-width: 110px; }
        }
        """

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Field Staff Pro</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
    <style>""" + css_style + """</style>
</head>
<body>

<div id="sidebar">
    <div style="padding: 16px; border-bottom: 1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
        <div style="font-weight: 700; font-size: 18px;">Field Staff Pro</div>
        <button class="mobile-only" onclick="Sidebar.toggle()" style="background:none; border:none; display:none;"><span class="material-icons-round">close</span></button>
    </div>
    
    <div class="filters">
        <div class="filter-group">
            <div class="filter-header">
                <span class="filter-label">Districts</span>
                <div class="filter-actions">
                    <button class="select-all-btn" onclick="App.toggleAll('f-dist', true)">All</button>
                    <button class="select-all-btn unselect" onclick="App.toggleAll('f-dist', false)">None</button>
                </div>
            </div>
            <div id="f-dist" class="multi-select-container"></div>
        </div>
        <div class="filter-group">
            <div class="filter-header">
                <span class="filter-label">Tehsils</span>
                <div class="filter-actions">
                    <button class="select-all-btn" onclick="App.toggleAll('f-tehsil', true)">All</button>
                    <button class="select-all-btn unselect" onclick="App.toggleAll('f-tehsil', false)">None</button>
                </div>
            </div>
            <div id="f-tehsil" class="multi-select-container"></div>
        </div>
        <div class="filter-group">
            <div class="filter-header">
                <span class="filter-label">MC/UC Areas</span>
                <div class="filter-actions">
                    <button class="select-all-btn" onclick="App.toggleAll('f-mc', true)">All</button>
                    <button class="select-all-btn unselect" onclick="App.toggleAll('f-mc', false)">None</button>
                </div>
            </div>
            <div id="f-mc" class="multi-select-container"></div>
        </div>
        <div style="display:flex; gap:12px;">
            <div class="filter-group" style="flex:1">
                <span class="filter-label">From</span>
                <input type="date" id="f-start" class="filter-select" style="padding:10px; border-radius:8px; border:1px solid #e2e8f0; font-size:13px; font-weight:500;">
            </div>
            <div class="filter-group" style="flex:1">
                <span class="filter-label">To</span>
                <input type="date" id="f-end" class="filter-select" style="padding:10px; border-radius:8px; border:1px solid #e2e8f0; font-size:13px; font-weight:500;">
            </div>
        </div>
    </div>

    <div style="display:flex; gap:12px; padding: 0 20px 10px 20px;">
        <button class="apply-btn" onclick="App.apply()" style="flex:1">
            <span class="material-icons-round">done_all</span> Apply
        </button>
        <button class="apply-btn" onclick="App.resetFilters()" style="flex:1; background:#ef4444; border-color:#ef4444">
            <span class="material-icons-round">refresh</span> Reset
        </button>
    </div>
    
    <div style="flex:1; overflow-y:auto; padding: 0 16px;">
        <button onclick="Stats.open()" class="secondary-btn">
             <span class="material-icons-round" style="color:var(--primary)">leaderboard</span> Leaderboard
        </button>
        <button onclick="PerformanceLog.open()" class="secondary-btn">
             <span class="material-icons-round" style="color:#8b5cf6">assignment_turned_in</span> Performance
        </button>
        <button onclick="ViewSwitcher.toList()" class="secondary-btn">
             <span class="material-icons-round" style="color:#06b6d4">view_list</span> Open List View
        </button>
    </div>

    <div class="stat-badge">
        <small>Markers Loaded</small>
        <span id="stat-count">0</span>
    </div>
</div>

<div id="main-stage">
    <div id="map-container">
        <div id="map"></div>
        
        <div class="map-controls">
            <div id="extra-ctrls" class="control-group">
                <button class="float-btn" onclick="Stats.open()" title="Leaderboard">
                    <span class="material-icons-round" style="color:#f59e0b">leaderboard</span>
                </button>
                <button class="float-btn" onclick="PerformanceLog.open()" title="Performance">
                    <span class="material-icons-round" style="color:#8b5cf6">assignment_turned_in</span>
                </button>
                <button class="float-btn" onclick="ViewSwitcher.toList()" title="List View">
                    <span class="material-icons-round" style="color:#06b6d4">view_list</span>
                </button>
                <button class="float-btn" onclick="App.toggleLayer()" title="Toggle Satellite">
                    <span class="material-icons-round" id="layer-icon">satellite_alt</span>
                </button>
                <button class="float-btn" onclick="State.map.zoomIn()" title="Zoom In">
                    <span class="material-icons-round">add</span>
                </button>
                <button class="float-btn" onclick="State.map.zoomOut()" title="Zoom Out">
                    <span class="material-icons-round">remove</span>
                </button>
                <button class="float-btn" onclick="Settings.open()" title="Settings">
                    <span class="material-icons-round" style="color:#10b981">settings</span>
                </button>
                <button class="float-btn" onclick="Sidebar.toggle()" title="Menu">
                    <span class="material-icons-round">menu</span>
                </button>
            </div>
            
            <button class="float-btn primary" onclick="App.toggleControls()" id="toggle-ctrls">
                <span class="material-icons-round">keyboard_arrow_down</span>
            </button>
        </div>
    </div>

    <!-- Persistent List View -->
    <div id="list-view-stage">
        <div class="list-nav">
            <button onclick="ViewSwitcher.toMap()" class="gal-btn" style="background:#f1f5f9; color:var(--text);"><span class="material-icons-round">map</span></button>
            <div style="font-weight:700">Record <span id="lv-idx">1</span> of <span id="lv-total">0</span></div>
            <div style="display:flex; gap:8px;">
                <button onclick="ListView.prev()" class="gal-btn" style="background:#f1f5f9; color:var(--text);"><span class="material-icons-round">chevron_left</span></button>
                <button onclick="ListView.next()" class="gal-btn" style="background:#f1f5f9; color:var(--text);"><span class="material-icons-round">chevron_right</span></button>
            </div>
        </div>
        <div class="record-card-container" style="flex:1; position:relative; overflow:hidden; display:flex; flex-direction:column;">
            <div id="lv-search-container" style="position:absolute; top:24px; right:calc(50% - 280px); z-index:1002;"></div>
            <div id="lv-content" class="record-card"></div>
        </div>
    </div>
</div>

<!-- Modals & Overlays -->
<div id="modal-stats" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:6000; align-items:center; justify-content:center; padding:20px;">
    <div style="background:white; border-radius:16px; width:100%; max-width:850px; height:90vh; display:flex; flex-direction:column;">
        <div style="padding:20px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
            <h3 style="margin:0" id="stats-title">Staff Performance</h3>
            <button onclick="Stats.close()" style="background:none; border:none; cursor:pointer;"><span class="material-icons-round">close</span></button>
        </div>
        <div id="stats-body" class="stats-table-container" style="flex:1; overflow-y:auto; padding:0;"></div>
    </div>
</div>

<div id="modal-log" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:6500; align-items:center; justify-content:center; padding:20px;">
    <div style="background:white; border-radius:16px; width:100%; max-width:950px; max-height:90vh; display:flex; flex-direction:column; box-shadow: 0 20px 50px rgba(0,0,0,0.2);">
        <div class="modal-header" style="padding:24px; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between; align-items:center; background: #fafafa; border-radius: 16px 16px 0 0;">
            <div style="display:flex; align-items:center; gap:12px;">
                <span class="material-icons-round" style="color:#8b5cf6; font-size:32px;">assignment_turned_in</span>
                <div>
                    <h3 style="margin:0; font-size: 20px;">Performance</h3>
                    <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
                        <small id="log-subtitle" style="color:#64748b; font-weight:600;"></small>
                        <div style="height:12px; width:1px; background:#e2e8f0;"></div>
                        <small id="data-start" style="color:#94a3b8; font-size:11px;"></small>
                    </div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="display:flex; align-items:center; gap:8px; background:#fff; border:1px solid #e2e8f0; padding:4px 12px; border-radius:8px;">
                    <small style="font-weight:700; color:#64748b;">Attendance From:</small>
                    <input type="date" id="att-start-date" onchange="PerformanceLog.updateDate(this.value)" style="border:none; font-family:inherit; font-weight:600; color:var(--primary); outline:none; cursor:pointer;">
                </div>
                <button onclick="PerformanceLog.close()" style="background:#f1f5f9; border:none; border-radius: 50%; width: 40px; height: 40px; display:flex; align-items:center; justify-content:center; cursor:pointer;"><span class="material-icons-round">close</span></button>
            </div>
        </div>
        <div id="log-body" class="stats-table-container" style="flex:1; overflow-y:auto; padding:0;"></div>
    </div>
</div>

<div id="gallery" class="gallery-overlay">
    <div class="gal-header">
        <button onclick="Gallery.close()" style="background:none; border:none; color:white; cursor:pointer;"><span class="material-icons-round" style="font-size:32px">close</span></button>
    </div>
    <div class="gal-viewport" id="gal-vp">
        <img id="gal-img" class="gal-img">
    </div>
    <div class="gal-controls">
        <button class="gal-btn" onclick="Gallery.rotate()"><span class="material-icons-round">rotate_right</span></button>
        <button class="gal-btn" onclick="Gallery.zoomOut()"><span class="material-icons-round">remove</span></button>
        <button class="gal-btn" onclick="Gallery.reset()"><span class="material-icons-round">refresh</span></button>
        <button class="gal-btn" onclick="Gallery.zoomIn()"><span class="material-icons-round">add</span></button>
    </div>
</div>

<div id="modal-settings" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:7000; align-items:center; justify-content:center; padding:20px;">
    <div style="background:white; border-radius:16px; width:100%; max-width:500px; display:flex; flex-direction:column; box-shadow: 0 20px 50px rgba(0,0,0,0.2);">
        <div style="padding:24px; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between; align-items:center; background: #fafafa; border-radius: 16px 16px 0 0;">
            <div style="display:flex; align-items:center; gap:12px;">
                <span class="material-icons-round" style="color:#10b981; font-size:32px;">settings</span>
                <h3 style="margin:0; font-size: 20px;">Settings</h3>
            </div>
            <button onclick="Settings.close()" style="background:#f1f5f9; border:none; border-radius: 50%; width: 40px; height: 40px; display:flex; align-items:center; justify-content:center; cursor:pointer;"><span class="material-icons-round">close</span></button>
        </div>
        <div style="padding:24px;">
            <div style="margin-bottom:24px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <label style="font-weight:700; font-size:14px; color:var(--text);">Map Marker Limit</label>
                    <span id="marker-limit-display" style="font-weight:800; font-size:18px; color:var(--primary);">999999</span>
                </div>
                <div style="font-size:12px; color:#64748b; margin-bottom:16px;">Control how many markers are displayed on the map for better performance.</div>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <button onclick="Settings.setMarkerLimit(5000)" class="secondary-btn" style="flex:1; min-width:100px; margin:0;">5,000</button>
                    <button onclick="Settings.setMarkerLimit(10000)" class="secondary-btn" style="flex:1; min-width:100px; margin:0;">10,000</button>
                    <button onclick="Settings.setMarkerLimit(20000)" class="secondary-btn" style="flex:1; min-width:100px; margin:0;">20,000</button>
                    <button onclick="Settings.setMarkerLimit(50000)" class="secondary-btn" style="flex:1; min-width:100px; margin:0;">50,000</button>
                    <button onclick="Settings.setMarkerLimit(999999)" class="secondary-btn" style="flex:1; min-width:100px; margin:0;">All</button>
                </div>
                <div style="margin-top:16px; display:flex; gap:8px;">
                    <button onclick="Settings.incrementMarkerLimit(-5000)" style="flex:1; padding:12px; border-radius:10px; border:1px solid #e2e8f0; background:white; font-weight:600; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px;">
                        <span class="material-icons-round">remove</span> -5,000
                    </button>
                    <button onclick="Settings.incrementMarkerLimit(5000)" style="flex:1; padding:12px; border-radius:10px; border:1px solid #e2e8f0; background:white; font-weight:600; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px;">
                        <span class="material-icons-round">add</span> +5,000
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
""" + embedded_data + """

<script>
    const State = {
        filtered: [],
        availableSurveyors: [], // For dropdown
        surveyorFilter: [], // Active filter - now array for multiple selection
        markers: L.layerGroup(),
        currentIdx: 0,
        map: null,
        markerLimit: 999999 // Default to maximum
    };

    const App = {
        init() {
            this.initMap();
            this.initFilters();
            this.apply(true); // Initial load
        },

        resetFilters() {
            State.surveyorFilter = [];
            document.getElementById('f-start').value = "";
            document.getElementById('f-end').value = "";
            this.initFilters();
            this.apply();
        },

        initMap() {
            State.map = L.map('map', { zoomControl: false }).setView([32.0836, 72.6711], 13);
            
            State.layers = {
                roads: L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
                    maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3']
                }),
                sat: L.tileLayer('https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
                    maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3']
                })
            };
            
            State.layers.roads.addTo(State.map);
            State.activeLayer = 'roads';
            State.markers.addTo(State.map);
        },

        toggleLayer() {
            const isRoads = State.activeLayer === 'roads';
            State.map.removeLayer(State.layers[State.activeLayer]);
            State.activeLayer = isRoads ? 'sat' : 'roads';
            State.layers[State.activeLayer].addTo(State.map);
            
            document.getElementById('layer-icon').innerText = isRoads ? 'map' : 'satellite_alt';
        },

        toggleControls() {
            const grp = document.getElementById('extra-ctrls');
            const btn = document.getElementById('toggle-ctrls').querySelector('.material-icons-round');
            const isCollapsed = grp.classList.toggle('collapsed');
            btn.innerText = isCollapsed ? 'keyboard_arrow_up' : 'keyboard_arrow_down';
        },

        initFilters() {
            const dists = Object.keys(HIERARCHY).sort();
            this.renderMultiSelect('f-dist', dists.map(d => ({ v: d, l: d })), 'onDistChange');
            
            // Set defaults: SARGODHA
            if(HIERARCHY['SARGODHA']) {
                this.setSelected('f-dist', ['SARGODHA']);
            } else if(dists.length > 0) {
                this.setSelected('f-dist', [dists[0]]);
            }
            
            this.onDistChange();
            
            // Set default Tehsil: SARGODHA
            const tItems = this.getMultiSelectItems('f-tehsil');
            if(tItems.some(item => item.value === 'SARGODHA')) {
                this.setSelected('f-tehsil', ['SARGODHA']);
            }
            this.onTehsilChange();

            // Set default MC: MC-1
            const mItems = this.getMultiSelectItems('f-mc');
            const targetMC = mItems.find(item => item.value.includes('MC-1') || item.value.includes('MC 1'));
            if(targetMC) {
                this.setSelected('f-mc', [targetMC.value]);
            }

            // Date defaults removed
            // const today = new Date().toISOString().split('T')[0];
            // document.getElementById('f-start').value = today;
            // document.getElementById('f-end').value = today;
        },

        renderMultiSelect(id, items, onUpdate) {
            const container = document.getElementById(id);
            container.innerHTML = items.map(item => `
                <div class="multi-option" data-value="${item.v}" onclick="App.handleMultiClick(event, '${id}, '${onUpdate}')">
                    <input type="checkbox" ${item.selected ? 'checked' : ''} onchange="App.handleMultiChange(event, '${id}, '${onUpdate}')">
                    <span>${item.l}</span>
                </div>
            `).join('');
        },

        // Dedicated robust MC/UC multi-select using DOM API
        renderMCUCSelect(items) {
            const container = document.getElementById('f-mc');
            container.innerHTML = ''; // Clear existing
            
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'multi-option';
                div.setAttribute('data-value', item.v);
                if(item.selected) div.classList.add('selected');
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = item.selected || false;
                checkbox.addEventListener('change', function() {
                    div.classList.toggle('selected', this.checked);
                });
                
                const span = document.createElement('span');
                span.textContent = item.l;
                
                div.appendChild(checkbox);
                div.appendChild(span);
                
                // Click on row toggles checkbox
                div.addEventListener('click', function(e) {
                    if (e.target !== checkbox) {
                        checkbox.checked = !checkbox.checked;
                        div.classList.toggle('selected', checkbox.checked);
                    }
                });
                
                container.appendChild(div);
            });
        },

        // Get selected MC/UC values
        getSelectedMCUC() {
            const container = document.getElementById('f-mc');
            const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
            return Array.from(checkboxes).map(cb => 
                cb.closest('.multi-option').getAttribute('data-value')
            );
        },


        handleMultiClick(e, id, onUpdate) {
            if(e.target.tagName === 'INPUT') return;
            const row = e.currentTarget;
            const cb = row.querySelector('input');
            cb.checked = !cb.checked;
            row.classList.toggle('selected', cb.checked);
            if(onUpdate && App[onUpdate]) App[onUpdate]();
        },

        handleMultiChange(e, id, onUpdate) {
            const row = e.target.closest('.multi-option');
            row.classList.toggle('selected', e.target.checked);
            if(onUpdate && App[onUpdate]) App[onUpdate]();
        },

        toggleAll(id, state) {
            const container = document.getElementById(id);
            const checkboxes = container.querySelectorAll('input');
            checkboxes.forEach(cb => {
                cb.checked = state;
                cb.closest('.multi-option').classList.toggle('selected', state);
            });
            
            if(id === 'f-dist') this.onDistChange();
            else if(id === 'f-tehsil') this.onTehsilChange();
        },

        getSelected(id) {
            const container = document.getElementById(id);
            return Array.from(container.querySelectorAll('.multi-option'))
                .filter(row => row.querySelector('input').checked)
                .map(row => row.getAttribute('data-value'));
        },

        getMultiSelectItems(id) {
             const container = document.getElementById(id);
             return Array.from(container.querySelectorAll('.multi-option')).map(row => ({
                 value: row.getAttribute('data-value')
             }));
        },

        setSelected(id, values) {
            const container = document.getElementById(id);
            container.querySelectorAll('.multi-option').forEach(row => {
                const val = row.getAttribute('data-value');
                const checked = values.includes(val);
                row.querySelector('input').checked = checked;
                row.classList.toggle('selected', checked);
            });
        },

        onDistChange() {
            const selectedDists = this.getSelected('f-dist');
            let items = [];
            
            selectedDists.forEach(d => {
                const tehsils = Object.keys(HIERARCHY[d] || {}).sort();
                tehsils.forEach(t => {
                    items.push({ v: t, l: `${d} - ${t}` });
                });
            });
            
            this.renderMultiSelect('f-tehsil', items);
            this.onTehsilChange();
        },

        onTehsilChange() {
            const items = this.getAvailableMCUCs();
            
            // Get CURRENT selections from DOM right before re-rendering
            const currentlySelected = this.getSelectedMCUC();
            
            items.forEach(item => {
                item.selected = currentlySelected.includes(item.v);
            });
            
            this.renderMCUCSelect(items);
        },

        getAvailableMCUCs() {
            const selectedDists = this.getSelected('f-dist');
            const selectedTehsils = this.getSelected('f-tehsil');
            let items = [];
            
            selectedDists.forEach(d => {
                const distData = HIERARCHY[d] || {};
                selectedTehsils.forEach(t => {
                    const tehsilData = distData[t] || {};
                    for(let m in tehsilData) {
                        items.push({ 
                            v: m, 
                            l: `${t} - ${tehsilData[m].s}`,
                            short: tehsilData[m].s
                        });
                    }
                });
            });
            
            items.sort((a, b) => {
                const aShort = a.short.toUpperCase();
                const bShort = b.short.toUpperCase();
                const aIsMC = aShort.startsWith('MC');
                const bIsMC = bShort.startsWith('MC');
                if(aIsMC && !bIsMC) return -1;
                if(!aIsMC && bIsMC) return 1;
                const aNum = parseInt(aShort.replace(/[^0-9]/g, '')) || 0;
                const bNum = parseInt(bShort.replace(/[^0-9]/g, '')) || 0;
                if(aNum !== bNum) return aNum - bNum;
                return a.l.localeCompare(b.l);
            });
            return items;
        },

        setSurveyorFilter(selectedValues) {
            // selectedValues is an array from multi-select
            State.surveyorFilter = selectedValues.length > 0 ? selectedValues : [];
            this.apply(); 
            // If in list view, re-render implies updating the current view
            if(document.getElementById('list-view-stage').classList.contains('active')) {
                State.currentIdx = 0;
                ListView.render();
            }
        },

        apply(isInitial = false) {
            const dists = this.getSelected('f-dist');
            const tehsils = this.getSelected('f-tehsil');
            const mcs = this.getSelectedMCUC();
            const s = document.getElementById('f-start').value;
            const e = document.getElementById('f-end').value;

            // 1. Geographical Filter
            let geoFiltered = RAW_DATA.filter(r => {
                if(dists.length > 0 && !dists.includes(r[10])) return false;
                if(tehsils.length > 0 && !tehsils.includes(r[11])) return false;
                if(mcs.length > 0 && !mcs.includes(r[12])) return false;
                if(s && r[7] < s) return false;
                if(e && r[7] > e) return false;
                return true;
            });

            // 2. Extract Available Surveyors from Geo Filtered Data
            State.availableSurveyors = [...new Set(geoFiltered.map(r => r[6]))].sort();

            // Auto-reset surveyor filter if not in new data
            if(State.surveyorFilter.length > 0) {
                State.surveyorFilter = State.surveyorFilter.filter(sf => State.availableSurveyors.includes(sf));
            }

            // 3. Apply Surveyor Filter
            if(State.surveyorFilter.length > 0) {
                State.filtered = geoFiltered.filter(r => State.surveyorFilter.includes(r[6]));
            } else {
                State.filtered = geoFiltered;
            }

            this.render();
            if(!isInitial) {
                // Only change view if not already in list view or if explicit apply
                if(!document.getElementById('list-view-stage').classList.contains('active')) {
                   Sidebar.toggle();
                   ViewSwitcher.toMap();
                }
            }
        },

        render() {
            State.markers.clearLayers();
            const bounds = L.latLngBounds();
            const totalCount = State.filtered.length;
            const displayCount = Math.min(totalCount, State.markerLimit);
            document.getElementById('stat-count').innerText = `${displayCount} / ${totalCount}`;

            // Use marker limit from settings
            State.filtered.slice(0, State.markerLimit).forEach(r => {
                // Skip records with invalid coordinates
                if (!r[1] || !r[2] || isNaN(r[1]) || isNaN(r[2])) {
                    console.warn('Skipping record with invalid coordinates:', r[0], 'lat:', r[1], 'lng:', r[2]);
                    return;
                }
                
                const color = HIERARCHY[r[10]]?.[r[11]]?.[r[12]]?.c || '#2563eb';
                const m = L.circleMarker([r[1], r[2]], {
                    radius: 5, fillColor: color, color: '#000', weight: 1.5, fillOpacity: 0.7
                });
                
                const imgs = r[9].map(url => `<img src="${url}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;cursor:pointer" onclick="Gallery.open('${url}', '${r[0]}')">`).join('');
                const popup = `
                    <div class="pop-card">
                        <div class="pop-title">ID: #${r[0]}</div>
                        <div style="font-size:12px; margin-bottom:8px">
                            <b>${r[6]}</b><br>
                            ${r[3]===1?'Commercial':'Domestic'} • ${r[8]}<br>
                            <small>${r[11]} - ${r[12]}</small>
                        </div>
                        <div style="display:flex; gap:4px; flex-wrap:wrap">${imgs}</div>
                    </div>
                `;
                m.bindPopup(popup);
                State.markers.addLayer(m);
                bounds.extend([r[1], r[2]]);
            });

            if(bounds.isValid()) State.map.fitBounds(bounds, {padding:[40,40]});
        }
    };

    const ViewSwitcher = {
        toList() {
            document.getElementById('list-view-stage').classList.add('active');
            State.currentIdx = 0;
            ListView.render();
            Sidebar.close();
        },
        toMap() {
            document.getElementById('list-view-stage').classList.remove('active');
        }
    };

    const ListView = {
        init() {
            this.renderFilters();
        },

        renderFilters() {
            const navFilter = document.getElementById('lv-search-container');
            if (!navFilter) return;

            // Store open state/focus if already exists
            const dd = document.getElementById('lv-surveyor-dropdown');
            const isVisible = dd && dd.style.display !== 'none';
            const searchVal = document.getElementById('lv-id-search')?.value || '';

            // 1. Surveyor Options
            let surveyorOptions = "";
            State.availableSurveyors.forEach(name => {
                const isChecked = State.surveyorFilter.includes(name);
                surveyorOptions += `
                    <div class="multi-option ${isChecked ? 'selected' : ''}" data-value="${name}" onclick="ListView.toggleSurveyor(event, '${name}')" style="padding:6px 10px; margin:2px 0;">
                        <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="ListView.handleSurveyorChange(event, '${name}')">
                        <span>${name}</span>
                    </div>
                `;
            });

            // 2. MC/UC Options
            const availableMCs = App.getAvailableMCUCs();
            const selectedMCs = App.getSelectedMCUC();
            let mcOptions = "";
            availableMCs.forEach(item => {
                const isChecked = selectedMCs.includes(item.v);
                mcOptions += `
                    <div class="multi-option ${isChecked ? 'selected' : ''}" data-value="${item.v}" onclick="ListView.toggleMCUC(event, '${item.v}')" style="padding:4px 10px; margin:2px 0; font-size:12px;">
                        <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="ListView.handleMCUCChange(event, '${item.v}')">
                        <span>${item.l}</span>
                    </div>
                `;
            });
            
            navFilter.innerHTML = `
                <div style="position:relative;">
                    <button onclick="ListView.toggleDropdown(event)" class="float-btn" style="background:#f1f5f9; color:var(--primary); box-shadow:none; width:40px; height:40px; border:1px solid #e2e8f0;">
                        <span class="material-icons-round">search</span>
                    </button>
                    <div id="lv-surveyor-dropdown" style="display:${isVisible ? 'block' : 'none'}; position:absolute; right:0; top:100%; margin-top:8px; background:white; border:1px solid #e2e8f0; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.15); max-height:800px; overflow-y:auto; min-width:280px; z-index:1001; padding:20px;">
                        <!-- ID Search -->
                        <div style="margin:10px 0 24px 0; display:flex; flex-direction:column; align-items:center;">
                            <div style="font-weight:700; font-size:11px; color:#94a3b8; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px; text-align:center;">Search Survey ID</div>
                            <input type="number" id="lv-id-search" placeholder="Enter ID..." 
                                value="${searchVal}"
                                onkeyup="if(event.key==='Enter') ListView.jumpToID(this.value)"
                                style="width:100%; padding:10px; border:1px solid #e2e8f0; border-radius:10px; font-size:14px; outline:none; font-family:inherit; text-align:center; background:#f8fafc; color:var(--text);">
                        </div>
                        
                        <!-- MC/UC Filter -->
                        <div style="margin-bottom:16px; border-top:1px solid #f1f5f9; padding-top:12px;">
                            <div style="font-weight:700; font-size:11px; color:#94a3b8; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;" id="lv-mcuc-count-label">Filter MC/UC (${selectedMCs.length || 'All'})</div>
                            <div style="display:flex; gap:6px; margin-bottom:8px;">
                                <button onclick="ListView.selectAllMCUCs(true)" class="select-all-btn" style="flex:1; padding:4px; font-size:10px;">All</button>
                                <button onclick="ListView.selectAllMCUCs(false)" class="select-all-btn unselect" style="flex:1; padding:4px; font-size:10px;">None</button>
                            </div>
                            <div style="max-height:120px; overflow-y:auto; border:1px solid #f8fafc; border-radius:8px; padding:4px; background:#f8fafc;">
                                ${mcOptions}
                            </div>
                        </div>

                        <!-- Surveyor Filter -->
                        <div style="border-top:1px solid #f1f5f9; padding-top:12px;">
                            <div style="font-weight:700; font-size:11px; color:#94a3b8; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;" id="lv-surveyor-count-label">Filter Surveyors (${State.surveyorFilter.length || 'All'})</div>
                            <div style="display:flex; gap:6px; margin-bottom:8px;">
                                <button onclick="ListView.selectAllSurveyors(true)" class="select-all-btn" style="flex:1; padding:4px; font-size:10px;">All</button>
                                <button onclick="ListView.selectAllSurveyors(false)" class="select-all-btn unselect" style="flex:1; padding:4px; font-size:10px;">None</button>
                            </div>
                            <div style="max-height:140px; overflow-y:auto; border:1px solid #f8fafc; border-radius:8px; padding:4px; background:#f8fafc;">
                                ${surveyorOptions}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add mobile search button adjustment
            if (!document.getElementById('lv-search-mobile-style')) {
                const style = document.createElement('style');
                style.id = 'lv-search-mobile-style';
                style.innerHTML = `
                    @media (max-width: 650px) {
                        #lv-search-container { right: 24px !important; }
                    }
                `;
                document.head.appendChild(style);
            }
        },

        render() {
            const r = State.filtered[State.currentIdx];
            const el = document.getElementById('lv-content');
            const total = State.filtered.length;
            
            document.getElementById('lv-idx').innerText = total > 0 ? State.currentIdx + 1 : 0;
            document.getElementById('lv-total').innerText = total;

            // Ensure filters are rendered if not already
            if (!document.getElementById('lv-surveyor-dropdown')) {
                this.renderFilters();
            }

            if(!r) { 
                el.innerHTML = `
                    <div class="card-header" style="display:flex; justify-content:center; align-items:center; height:200px;">
                        <div class="card-title" style="color:#64748b">No records match the current filters.</div>
                    </div>`; 
                return; 
            }

            // Contextual Naming
            const dists = App.getSelected('f-dist');
            const tehsils = App.getSelected('f-tehsil');
            let displayName = r[6];
            if(tehsils.length > 1 || dists.length > 1) {
                displayName += ` (${r[11]})`;
            }

            el.innerHTML = `
                <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="flex:1; min-width:0; padding-right:50px;">
                        <div class="card-title">Survey ID #${r[0]}</div>
                        <div style="color:var(--primary); font-weight:600; font-size:14px; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${displayName}</div>
                    </div>
                </div>
                <div class="card-grid">
                    <div class="grid-item" style="grid-column: span 2"><span class="grid-label">Name</span><span class="grid-val">${r[4]}</span></div>
                    <div class="grid-item"><span class="grid-label">Type</span><span class="grid-val">${r[3]===1?'Commercial':'Domestic'}</span></div>
                    <div class="grid-item"><span class="grid-label">Time</span><span class="grid-val">${r[8]}</span></div>
                    <div class="grid-item"><span class="grid-label">Date</span><span class="grid-val">${r[7]}</span></div>
                    <div class="grid-item"><span class="grid-label">House</span><span class="grid-val">${r[13] || 'N/A'}</span></div>
                    <div class="grid-item" style="grid-column: span 2"><span class="grid-label">Address</span><span class="grid-val">${r[5]}</span></div>
                    <div class="grid-item" style="grid-column: span 2"><span class="grid-label">Area</span><span class="grid-val">${r[11]} - ${r[12]}</span></div>
                </div>
                <div class="card-gallery">
                    ${r[9].map(url => `<img src="${url}" class="gallery-thumb" onclick="Gallery.open('${url}', '${r[0]}')">`).join('')}
                </div>
            `;
        },
        next() { if(State.currentIdx < State.filtered.length - 1) { State.currentIdx++; this.render(); }},
        prev() { if(State.currentIdx > 0) { State.currentIdx--; this.render(); }},
        
        toggleDropdown(e) {
            if (e) e.stopPropagation();
            const dd = document.getElementById('lv-surveyor-dropdown');
            const isVisible = dd.style.display !== 'none';
            
            if (isVisible) {
                dd.style.display = 'none';
                document.removeEventListener('click', this._outsideClickHandler);
            } else {
                dd.style.display = 'block';
                // Focus the ID search box
                setTimeout(() => {
                    const searchInput = document.getElementById('lv-id-search');
                    if(searchInput) searchInput.focus();
                }, 10);

                this._outsideClickHandler = (e) => {
                    if (!dd.contains(e.target) && !e.target.closest('button[onclick*="toggleDropdown"]')) {
                        dd.style.display = 'none';
                        document.removeEventListener('click', this._outsideClickHandler);
                    }
                };
                document.addEventListener('click', this._outsideClickHandler);
            }
        },

        jumpToID(id) {
            if(!id) return;
            const idx = State.filtered.findIndex(r => r[0].toString() === id.toString());
            if (idx !== -1) {
                State.currentIdx = idx;
                this.render();
                // Close dropdown after jump
                const dd = document.getElementById('lv-surveyor-dropdown');
                if(dd) dd.style.display = 'none';
            } else {
                alert('Survey ID #' + id + ' not found in current filtered results.');
            }
        },
        
        toggleSurveyor(e, name) {
            if(e.target.tagName === 'INPUT') return;
            const row = e.currentTarget;
            const cb = row.querySelector('input');
            cb.checked = !cb.checked;
            row.classList.toggle('selected', cb.checked);
            this.updateSurveyorFilter();
        },
        
        handleSurveyorChange(e, name) {
            const row = e.target.closest('.multi-option');
            row.classList.toggle('selected', e.target.checked);
            this.updateSurveyorFilter();
        },
        
        selectAllSurveyors(selectAll) {
            const dd = document.getElementById('lv-surveyor-dropdown');
            const checkboxes = dd.querySelectorAll('#lv-surveyor-dropdown div[onclick*="toggleSurveyor"] input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = selectAll;
                cb.closest('.multi-option').classList.toggle('selected', selectAll);
            });
            this.updateSurveyorFilter();
        },

        toggleMCUC(e, val) {
            if(e.target.tagName === 'INPUT') return;
            const row = e.currentTarget;
            const cb = row.querySelector('input');
            cb.checked = !cb.checked;
            row.classList.toggle('selected', cb.checked);
            this.updateMCUCFilter();
        },

        handleMCUCChange(e, val) {
            const row = e.target.closest('.multi-option');
            row.classList.toggle('selected', e.target.checked);
            this.updateMCUCFilter();
        },

        selectAllMCUCs(selectAll) {
            const dd = document.getElementById('lv-surveyor-dropdown');
            const checkboxes = dd.querySelectorAll('#lv-surveyor-dropdown div[onclick*="toggleMCUC"] input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = selectAll;
                cb.closest('.multi-option').classList.toggle('selected', selectAll);
            });
            this.updateMCUCFilter();
        },
        
        updateSurveyorFilter() {
            const dd = document.getElementById('lv-surveyor-dropdown');
            if (!dd) return;
            const checkboxes = dd.querySelectorAll('#lv-surveyor-dropdown div[onclick*="toggleSurveyor"] input[type="checkbox"]:checked');
            const selected = Array.from(checkboxes).map(cb => cb.closest('.multi-option').getAttribute('data-value'));
            
            State.surveyorFilter = selected.length > 0 ? selected : [];
            App.apply();
            
            State.currentIdx = 0;
            this.render();

            const countLabel = document.getElementById('lv-surveyor-count-label');
            if (countLabel) {
                countLabel.innerText = `Filter Surveyors (${selected.length || 'All'})`;
            }
        },

        updateMCUCFilter() {
            const dd = document.getElementById('lv-surveyor-dropdown');
            if (!dd) return;
            const checkboxes = dd.querySelectorAll('#lv-surveyor-dropdown div[onclick*="toggleMCUC"] input[type="checkbox"]:checked');
            const selected = Array.from(checkboxes).map(cb => cb.closest('.multi-option').getAttribute('data-value'));
            
            // Sync to sidebar
            App.setSelected('f-mc', selected);
            App.apply();
            
            State.currentIdx = 0;
            this.render();

            // Manually update the count label
            const countLabel = document.getElementById('lv-mcuc-count-label');
            if (countLabel) {
                countLabel.innerText = `Filter MC/UC (${selected.length || 'All'})`;
            }

            // Since MC/UC change might change available surveyors, update surveyor options in DD without closing
            // But to be 100% persistent, we just update the DOM elements for surveyors if they changed
            // For now, let's keep it simple: if surveyors changed, we might need a partial re-render of that section
            // However, typical flow is MC/UC selection first.
            this.syncSurveyorOptions();
        },

        syncSurveyorOptions() {
            // Partial update of the surveyor list in the dropdown
            const dd = document.getElementById('lv-surveyor-dropdown');
            if (!dd) return;
            
            const surveyorScrollArea = dd.querySelector('div[onclick*="toggleSurveyor"]')?.parentElement;
            if (!surveyorScrollArea) return;

            let surveyorOptions = "";
            State.availableSurveyors.forEach(name => {
                const isChecked = State.surveyorFilter.includes(name);
                surveyorOptions += `
                    <div class="multi-option ${isChecked ? 'selected' : ''}" data-value="${name}" onclick="ListView.toggleSurveyor(event, '${name}')" style="padding:6px 10px; margin:2px 0;">
                        <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="ListView.handleSurveyorChange(event, '${name}')">
                        <span>${name}</span>
                    </div>
                `;
            });
            surveyorScrollArea.innerHTML = surveyorOptions;

            const countLabel = document.getElementById('lv-surveyor-count-label');
            if (countLabel) {
                countLabel.innerText = `Filter Surveyors (${State.surveyorFilter.length || 'All'})`;
            }
        }
    };

    const Stats = {
        open() {
            const dataByName = {};
            State.filtered.forEach(r => {
                const name = r[6];
                if(!dataByName[name]) dataByName[name] = [];
                dataByName[name].push(r);
            });

            // Sort staff by count
            const sorted = Object.entries(dataByName).sort((a,b) => b[1].length - a[1].length);
            
            // Dynamic Heading
            const dists = App.getSelected('f-dist').join(', ') || 'All';
            const tehsils = App.getSelected('f-tehsil').join(', ') || 'All';
            document.getElementById('stats-title').innerText = `Performance: ${dists} (${tehsils})`;

            let html = `<table style="width:100%; border-collapse:collapse; font-size:12px; min-width:650px;">
                <thead style="background:#f8fafc; position:sticky; top:0; z-index:10;">
                    <tr>
                        <th style="padding:8px; text-align:center; width: 80px;">Count</th>
                        <th style="padding:8px; text-align:left;">Staff</th>
                        <th style="padding:8px; text-align:center;">Idle</th>
                        <th style="padding:8px; text-align:center;">First / Last</th>
                        <th style="padding:8px; text-align:center;">Status</th>
                    </tr>
                </thead>
                <tbody>`;

            sorted.forEach(([name, records], i) => {
                // Calculate Stats Dynamically for the filtered range
                const sortedRecs = records.slice().sort((a,b) => a[8].localeCompare(b[8]));
                const first = sortedRecs[0][8];
                const last = sortedRecs[sortedRecs.length - 1][8];
                
                let warn = 0, idle = 0;
                const windowStart = "10:00:00";
                const windowEnd = "17:00:00";
                const shutdownCutoff = "16:55:00";

                for(let j=1; j<sortedRecs.length; j++) {
                    const t1 = sortedRecs[j-1][8];
                    const t2 = sortedRecs[j][8];
                    if(t1 < windowStart || t1 > windowEnd) continue;
                    
                    const d1 = new Date(`2000-01-01T${t1}`);
                    const d2 = new Date(`2000-01-01T${t2}`);
                    let diff = (d2 - d1) / 60000;
                    
                    const lStart = new Date(`2000-01-01T13:00:00`);
                    const lEnd = new Date(`2000-01-01T14:00:00`);
                    const overlapStart = new Date(Math.max(d1, lStart));
                    const overlapEnd = new Date(Math.min(d2, lEnd));
                    if(overlapEnd > overlapStart) diff -= (overlapEnd - overlapStart) / 60000;

                    if(diff > 60) idle++;
                    else if(diff > 30) warn++;
                }

                // Tiered Trophies
                let trophy = "";
                if(i === 0) trophy = `<span class="trophy gold">🏆</span>`;
                else if(i === 1) trophy = `<span class="trophy silver">🥈</span>`;
                else if(i < 5) trophy = `<span class="trophy bronze">🥉</span>`;

                let statusMsg = '<span class="status-msg status-ok">Active</span>';
                if(idle > 0) statusMsg = '<span class="status-msg status-idle">Idle!</span>';
                else if(warn > 0) statusMsg = '<span class="status-msg status-warn">Delay</span>';
                
                const countClass = records.length > 100 ? 'count-high' : '';
                const idleClass = idle > 0 ? 'idle-danger' : (warn > 0 ? 'idle-warn' : '');
                const lastClass = last < shutdownCutoff ? 'time-warning' : '';
                
                html += `<tr class="rank-row" style="${i === 0 ? 'height: 60px;' : ''}">
                    <td style="padding:8px; text-align:center;">
                        <span class="count-badge ${countClass}">${records.length}</span>
                    </td>
                    <td style="padding:8px; font-weight:700;">${name}${trophy}</td>
                    <td style="padding:8px; text-align:center;" class="${idleClass}">${idle + warn}</td>
                    <td style="padding:8px; text-align:center; font-size:12px; color:#475569;">
                        <b>${first}</b><br><span class="${lastClass}">${last}</span>
                    </td>
                    <td style="padding:8px; text-align:center;">${statusMsg}</td>
                </tr>`;
            });
            
            html += `</tbody></table>`;
            document.getElementById('stats-body').innerHTML = html;
            document.getElementById('modal-stats').style.display = 'flex';
        },
        close() { document.getElementById('modal-stats').style.display = 'none'; }
    };

    const Gallery = {
        scale: 1, rot: 0,
        images: [], idx: 0, touchStartX: 0,

        open(src, surveyId) {
            // Find survey to populate image list
            const record = RAW_DATA.find(r => r[0] == surveyId);
            this.images = record ? record[9] : [src];
            this.idx = this.images.indexOf(src);
            if(this.idx === -1) this.idx = 0;

            this.showImage();
            document.getElementById('gallery').classList.add('active');
        },
        
        showImage() {
            document.getElementById('gal-img').src = this.images[this.idx];
            this.reset();
        },

        next() {
            this.idx = (this.idx + 1) % this.images.length;
            this.showImage();
        },

        prev() {
            this.idx = (this.idx - 1 + this.images.length) % this.images.length;
            this.showImage();
        },

        clickNav(e) {
            if(e.target.tagName !== 'IMG' && e.target.id !== 'gal-vp') return;
            const width = document.getElementById('gal-vp').clientWidth;
            // use clientX relative to viewport rect to handle potential offsets
            const rect = document.getElementById('gal-vp').getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            
            if(clickX > width / 2) this.next();
            else this.prev();
        },

        close() { document.getElementById('gallery').classList.remove('active'); },
        rotate() { this.rot += 90; this.update(); },
        zoomIn() { this.scale += 0.2; this.update(); },
        zoomOut() { if(this.scale > 0.4) { this.scale -= 0.2; this.update(); }},
        reset() { this.scale = 1; this.rot = 0; this.update(); },
        update() {
            document.getElementById('gal-img').style.transform = `scale(${this.scale}) rotate(${this.rot}deg)`;
        }
    };
    
    // Attach Gallery Events
    const galVp = document.getElementById('gal-vp');
    galVp.addEventListener('click', e => Gallery.clickNav(e));
    galVp.addEventListener('touchstart', e => Gallery.touchStartX = e.changedTouches[0].screenX);
    galVp.addEventListener('touchend', e => {
        const diff = Gallery.touchStartX - e.changedTouches[0].screenX;
        if(Math.abs(diff) > 40) diff > 0 ? Gallery.next() : Gallery.prev();
    });

    const Sidebar = {
        toggle() { document.getElementById('sidebar').classList.toggle('open'); },
        close() { document.getElementById('sidebar').classList.remove('open'); }
    };

    const Settings = {
        open() {
            this.updateDisplay();
            document.getElementById('modal-settings').style.display = 'flex';
        },
        
        close() {
            document.getElementById('modal-settings').style.display = 'none';
        },
        
        setMarkerLimit(limit) {
            State.markerLimit = limit;
            this.updateDisplay();
            App.render();
        },
        
        incrementMarkerLimit(amount) {
            const newLimit = Math.max(5000, State.markerLimit + amount);
            State.markerLimit = newLimit;
            this.updateDisplay();
            App.render();
        },
        
        updateDisplay() {
            const display = State.markerLimit >= 999999 ? 'All' : State.markerLimit.toLocaleString();
            document.getElementById('marker-limit-display').innerText = display;
        }
    };

    // Keyboard support for List View
    window.addEventListener('keydown', e => {
        if(!document.getElementById('list-view-stage').classList.contains('active')) return;
        if(e.key === 'ArrowRight') ListView.next();
        if(e.key === 'ArrowLeft') ListView.prev();
    });

    // Touch support for List View
    let touchStartX = 0;
    document.getElementById('lv-content').addEventListener('touchstart', e => touchStartX = e.changedTouches[0].screenX);
    document.getElementById('lv-content').addEventListener('touchend', e => {
        const diff = touchStartX - e.changedTouches[0].screenX;
        if(Math.abs(diff) > 50) diff > 0 ? ListView.next() : ListView.prev();
    });

    const PerformanceLog = {
        customStartDate: null,
        
        getDataStartDate() {
            if(!RAW_DATA.length) return null;
            return RAW_DATA[0][7]; // Using Date column
        },

        calcWorkingDays(start, end) {
            let count = 0;
            let current = new Date(start);
            const last = new Date(end);
            while(current <= last) {
                if(current.getDay() !== 0) count++; // Not Sunday
                current.setDate(current.getDate() + 1);
            }
            return count;
        },

        updateDate(val) {
            this.customStartDate = val;
            this.open();
        },

        open() {
            // 1. Setup Dates & Working Day Range
            const dataStart = this.getDataStartDate();
            const today = new Date().toISOString().split('T')[0];
            
            if(!this.customStartDate) {
                const now = new Date();
                this.customStartDate = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-01`;
            }
            document.getElementById('att-start-date').value = this.customStartDate;
            document.getElementById('data-start').innerText = `Data from: ${dataStart}`;

            const workingDays = [];
            let curr = new Date(this.customStartDate);
            while(curr <= new Date(today)) {
                if(curr.getDay() !== 0) workingDays.push(curr.toISOString().split('T')[0]);
                curr.setDate(curr.getDate() + 1);
            }

            // 2. Pre-calculate MONTHLY STATS (ignoring map filters) using RAW_DATA
            const staffMonthly = {};
            const fullHistory = {}; // [Staff][Date] = Records
            
            RAW_DATA.forEach(r => {
                const staff = r[6], d = r[7];
                if(d < this.customStartDate || d > today) return;
                if(!fullHistory[staff]) fullHistory[staff] = {};
                if(!fullHistory[staff][d]) fullHistory[staff][d] = [];
                fullHistory[staff][d].push(r);
            });

            const uniqueStaffInView = [...new Set(State.filtered.map(r => r[6]))];
            const totalWorkingDaysCount = workingDays.length;

            uniqueStaffInView.forEach(sh => {
                let absences = 0;
                const datesWithData = Object.keys(fullHistory[sh] || {});
                
                datesWithData.forEach(d => {
                    const dayRecs = fullHistory[sh][d];
                    // Calculate score for that day to see if it was -3
                    const total = dayRecs.length;
                    const pmCount = dayRecs.filter(r => r[8] >= "14:00:00" && r[8] <= "16:55:00").length;
                    let idleCount = 0;
                    const sorted = dayRecs.sort((a,b) => a[8].localeCompare(b[8]));
                    for(let i=1; i<sorted.length; i++) {
                        const t1 = sorted[i-1][8], t2 = sorted[i][8];
                        if(t1 < "10:00:00" || t1 > "16:55:00") continue;
                        const d1 = new Date(`2000-01-01T${t1}`), d2 = new Date(`2000-01-01T${t2}`);
                        let diff = (d2 - d1) / 60000;
                        const lS = new Date(`2000-01-01T13:00:00`), lE = new Date(`2000-01-01T14:00:00`);
                        const oS = new Date(Math.max(d1, lS)), oE = new Date(Math.min(d2, lE));
                        if(oE > oS) diff -= (oE - oS) / 60000;
                        if(diff > 30) idleCount++;
                    }
                    let score = 0;
                    if(total < 100) score -= 1;
                    if(pmCount < 30) score -= 1;
                    if(idleCount > 3) score -= 1;
                    
                    if(score === -3) absences++;
                });

                staffMonthly[sh] = { 
                    abs: absences, 
                    pres: totalWorkingDaysCount - absences 
                };
            });

            // 3. Process CURRENT FILTERED VIEW for Daily Rows
            const grouped = {};
            State.filtered.forEach(r => {
                const name = r[6], date = r[7];
                if(!grouped[name]) grouped[name] = {};
                if(!grouped[name][date]) grouped[name][date] = [];
                grouped[name][date].push(r);
            });

            const rows = [];
            for(let name in grouped) {
                for(let date in grouped[name]) {
                    const recs = grouped[name][date].sort((a,b) => a[8].localeCompare(b[8]));
                    const total = recs.length;
                    
                    // PM Count (14:00 - 16:55)
                    const pmCount = recs.filter(r => r[8] >= "14:00:00" && r[8] <= "16:55:00").length;
                    
                    // Idle Count (10:00 - 16:55)
                    let idleCount = 0;
                    const winStart = "10:00:00", winEnd = "16:55:00";
                    for(let i=1; i<recs.length; i++) {
                        const t1 = recs[i-1][8], t2 = recs[i][8];
                        if(t1 < winStart || t1 > winEnd) continue;
                        
                        const d1 = new Date(`2000-01-01T${t1}`), d2 = new Date(`2000-01-01T${t2}`);
                        let diff = (d2 - d1) / 60000;
                        
                        // Lunch correction
                        const lS = new Date(`2000-01-01T13:00:00`), lE = new Date(`2000-01-01T14:00:00`);
                        const oS = new Date(Math.max(d1, lS)), oE = new Date(Math.min(d2, lE));
                        if(oE > oS) diff -= (oE - oS) / 60000;
                        
                        if(diff > 30) idleCount++;
                    }

                    // Score Logic (All penalties now -1)
                    let score = 0;
                    if(total < 100) score -= 1;
                    if(pmCount < 30) score -= 1;
                    if(idleCount > 3) score -= 1;

                    rows.push({ name, date, total, pmCount, idleCount, score });
                }
            }


            // Sort by Date then Score
            rows.sort((a,b) => b.date.localeCompare(a.date) || a.score - b.score);


            const dists = App.getSelected('f-dist').join(', ') || 'All';
            document.getElementById('log-subtitle').innerText = `Analysis for: ${dists}`;

            let html = `
                <div class="guide-box">
                    <h4>Rules</h4>
                    <div class="guide-box-content">
                        <div class="guide-item" style="border-left: 3px solid #3b82f6">
                            <i class="material-icons-round" style="color:#3b82f6">fact_check</i>
                            <b>100 daily minimum Survey</b> <span class="penalty">-1</span>
                        </div>
                        <div class="guide-item" style="border-left: 3px solid #8b5cf6">
                            <i class="material-icons-round" style="color:#8b5cf6">query_builder</i>
                            <b>2pm to 5pm = minimum 30 Survey</b> <span class="penalty">-1</span>
                        </div>
                        <div class="guide-item" style="border-left: 3px solid #f59e0b">
                            <i class="material-icons-round" style="color:#f59e0b">timer_off</i>
                            <b>idle = no survey for 30 minute</b> <span class="penalty">-1</span>
                        </div>
                    </div>
                    <div style="margin-top:10px; font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">* Failing all 3 = ABSENCE</div>
                </div>
                <table class="perf-table" style="width:100%; border-collapse:collapse; font-size:14px; min-width:800px;">
                <thead style="background:#f8fafc; position:sticky; top:0; z-index:20;">
                    <tr>
                        <th style="padding:16px; text-align:left;">Staff / Date</th>
                        <th style="padding:16px; text-align:center;">Final Status</th>
                        <th style="padding:16px; text-align:center;">Daily Total</th>
                        <th style="padding:16px; text-align:center;">PM Count (2-5)</th>
                        <th style="padding:16px; text-align:center;">Idle Warnings</th>
                        <th style="padding:16px; text-align:center;">Score</th>
                        <th style="padding:16px; text-align:center;">Total Absents</th>
                        <th style="padding:16px; text-align:center;">Monthly Attendance</th>
                    </tr>
                </thead>
                <tbody>`;

            rows.forEach(r => {
                const isAbsence = r.score === -3;
                const scoreColor = r.score < 0 ? 'var(--danger)' : 'var(--text)';
                const statusClass = isAbsence ? 'status-idle' : 'status-ok';
                const statusText = isAbsence ? 'ABSENCE' : 'PRESENT';
                const stats = staffMonthly[r.name] || { abs: 0, pres: 0 };
                const absComp = stats.abs > 0 ? `<span style="color:var(--danger)">-${stats.abs}</span>` : '0';
                const attDisplay = `<b>${stats.pres}</b> / ${absComp}`;

                html += `<tr class="rank-row">
                    <td style="padding:16px;">
                        <div style="font-weight:700">${r.name}</div>
                        <div style="font-size:12px; color:#64748b">${r.date}</div>
                    </td>
                    <td style="padding:16px; text-align:center;">
                        <span class="status-msg ${statusClass}" style="padding:6px 12px; font-size:11px;">${statusText}</span>
                    </td>
                    <td style="padding:16px; text-align:center;">
                        <div class="score-box">
                            <span class="count-badge ${r.total < 100 ? 'idle-danger' : 'count-high'}">${r.total}</span>
                            <i class="material-icons-round ${r.total < 100 ? 'fail-mark' : 'pass-mark'}">check_circle</i>
                        </div>
                    </td>
                    <td style="padding:16px; text-align:center;">
                        <div class="score-box">
                            <span style="font-weight:700; color:${r.pmCount < 30 ? 'var(--danger)' : 'var(--text)'}">${r.pmCount}</span>
                            <i class="material-icons-round ${r.pmCount < 30 ? 'fail-mark' : 'pass-mark'}">check_circle</i>
                        </div>
                    </td>
                    <td style="padding:16px; text-align:center;">
                        <div class="score-box">
                            <span style="font-weight:700; color:${r.idleCount > 3 ? 'var(--danger)' : 'var(--text)'}">${r.idleCount}</span>
                            <i class="material-icons-round ${r.idleCount > 3 ? 'fail-mark' : 'pass-mark'}">check_circle</i>
                        </div>
                    </td>
                    <td style="padding:16px; text-align:center; font-weight:800; color:${scoreColor}">${r.score > 0 ? '+' : ''}${r.score}</td>
                    <td style="padding:16px; text-align:center;">
                        <span style="font-weight:700; color:${stats.abs > 0 ? 'var(--danger)' : 'var(--text)'}">${stats.abs}</span>
                        <div style="font-size:10px; color:#94a3b8; font-weight:700">ABSENTS</div>
                    </td>
                    <td style="padding:16px; text-align:center;">
                        <div style="font-size:14px;">${attDisplay}</div>
                        <small style="font-size:10px; color:#94a3b8; font-weight:700">ATTENDANCE</small>
                    </td>
                </tr>`;
            });

            html += `</tbody></table>`;
            document.getElementById('log-body').innerHTML = html;
            document.getElementById('modal-log').style.display = 'flex';
        },
        close() { document.getElementById('modal-log').style.display = 'none'; }
    };

    window.onload = () => App.init();
</script>
</body>
</html>"""

        
        # Fix the regex pattern that got double-escaped
        html = html.replace(r'/\\\\\\\\d+/', r'/\d+/')
        html = html.replace(r'/\\\\d+/', r'/\d+/')
        
        output_path = os.path.join(OUTPUT_DIR, output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"Generated {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    generator = ModernMapGenerator()
    if generator.process_csvs():
        generator.generate_html("modern_map.html")
