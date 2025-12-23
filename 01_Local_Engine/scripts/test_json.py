import json

# Test JSON escaping
test_data = [
    {
        "survey_id": "SGD-001",
        "district": "Sargodha",
        "tehsil": "Sargodha",
        "mc_uc": "Sargodha - MC-1",
        "consumer_type": "Domestic",
        "consumer_name": "Test User",
        "location": "32.0833,72.6667",
        "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
    }
]

# Properly escape JSON data for JavaScript embedding
survey_data_json = json.dumps(test_data).replace('\\', '\\\\').replace('"', '\\"')
print("Escaped JSON:")
print(survey_data_json)

# Test parsing
print("\nTesting JavaScript parsing:")
js_code = f'var surveyData = JSON.parse("{survey_data_json}");'
print(js_code)