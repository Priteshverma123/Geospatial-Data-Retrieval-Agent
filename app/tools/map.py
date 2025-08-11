import requests
from datetime import datetime, timedelta

def get_evalscript_for_layer(layer: str) -> str:
    """
    Returns a pre-defined evalscript for a specific analysis layer.
    """
    if layer.upper() == "TRUE_COLOR":
        return """
        //VERSION=3
        function setup() {
          return {
            input: ["B04", "B03", "B02"],
            output: { bands: 3 }
          };
        }
        function evaluatePixel(sample) {
          let r = Math.pow((sample.B04 - 0.05) / (0.4 - 0.05), 0.8);
          let g = Math.pow((sample.B03 - 0.05) / (0.4 - 0.05), 0.8);
          let b = Math.pow((sample.B02 - 0.05) / (0.4 - 0.05), 0.8);
          return [
            Math.max(0, Math.min(1, r)),
            Math.max(0, Math.min(1, g)),
            Math.max(0, Math.min(1, b))
          ];
        }
        """
    elif layer == "CLOUDS":
        return """
        //VERSION=3
        function setup() {
          return { input: ["B01", "B02", "B03"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
          return [sample.B01 * 4.0, sample.B02 * 4.0, sample.B03 * 4.0]; // Clouds pop bright
        }
        """
    elif layer == "SNOW":
        return """
        //VERSION=3
        function setup() {
          return { input: ["B03", "B11"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
          let ndsi = (sample.B03 - sample.B11) / (sample.B03 + sample.B11);
          return [ndsi, ndsi, ndsi]; // Snow appears bright
        }
        """

    elif layer.upper() == "VEGETATION":
        return """
        //VERSION=3
        function setup() {
        return {
            input: ["B04", "B08"],
            output: { bands: 3 }
        };
        }
        function evaluatePixel(sample) {
        let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
        
        // Apply color mapping
        if (ndvi < 0)         return [0.5, 0.5, 0.5];  // Gray: bare soil or water
        else if (ndvi < 0.2)  return [0.8, 0.6, 0.3];  // Brownish: sparse vegetation
        else if (ndvi < 0.4)  return [0.6, 0.8, 0.2];  // Yellow-green: moderate vegetation
        else if (ndvi < 0.6)  return [0.2, 0.7, 0.2];  // Green: dense vegetation
        else                  return [0.0, 0.5, 0.0];  // Dark green: very dense

        }
        """

    elif layer.upper() == "WATER":
        return """
        //VERSION=3
        function setup() {
        return {
            input: ["B03", "B08"],
            output: { bands: 3 }
        };
        }
        function evaluatePixel(sample) {
        let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);

        // Color map for water detection
        if (ndwi < 0)         return [0.3, 0.2, 0.1];  // Dry / land areas (brownish)
        else if (ndwi < 0.2)  return [0.4, 0.5, 0.7];  // Damp / transitional
        else if (ndwi < 0.4)  return [0.2, 0.4, 0.9];  // Shallow water
        else                  return [0.0, 0.2, 1.0];  // Deep water: intense blue
        }
        """

    elif layer.upper() == "MOISTURE":
        return """
        //VERSION=3
        function setup() {
          return {
            input: ["B08", "B11"],
            output: { bands: 3 }
          };
        }
        function evaluatePixel(sample) {
          let ndmi = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
          ndmi = (ndmi + 1) / 2;
          return [ndmi * 0.2, ndmi * 0.4, ndmi * 0.7];
        }
        """

    elif layer.upper() == "FLOOD":
        return """
        //VERSION=3
        function setup() {
          return {
            input: ["B03", "B08", "B11"],
            output: { bands: 3 }
          };
        }
        function evaluatePixel(sample) {
          let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
          let ndmi = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
          ndwi = (ndwi + 1) / 2;
          ndmi = (ndmi + 1) / 2;
          return [ndwi * 0.5, ndmi * 0.5, ndwi];
        }
        """
    elif layer == "URBAN":
        return """
        //VERSION=3
        function setup() {
          return { input: ["B12", "B11", "B04"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
          return [2.5 * sample.B12, 2.5 * sample.B11, 2.5 * sample.B04];
        }
        """

    else:
        # Default: simple True Color fallback
        return """
        //VERSION=3
        function setup() {
          return {
            input: ["B04", "B03", "B02"],
            output: { bands: 3 }
          };
        }
        function evaluatePixel(sample) {
          return [sample.B04, sample.B03, sample.B02];
        }
        """




def get_satellite_image_and_save(latitude: float, longitude: float, date: str, layer: str, file_name: str) -> str:
    CLIENT_ID = "2c9a965e-3a2f-40d8-acbb-e40a28f7f4fc"  # Replace this with your client ID
    CLIENT_SECRET = "RRV5Z2Ogk4w1qpUgrUxsMvcpYXz2aK2Y"  # Replace this with your client secret

    # Step 1: Get Auth Token
    auth_url = 'https://services.sentinel-hub.com/oauth/token'
    auth_payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    auth_response = requests.post(auth_url, data=auth_payload)
    if auth_response.status_code == 200:
        access_token = auth_response.json().get('access_token')
        print("Access token obtained successfully.")
    else:
        return f"Auth Failed: {auth_response.text}"

    evalscript = get_evalscript_for_layer(layer)

    # Step 2: Define the request for Sentinel-2 imagery
    bbox = [longitude - 0.5, latitude - 0.5, longitude + 0.5, latitude + 0.5]  # Increased bounding box
    date_obj = datetime.strptime(date, "%Y-%m-%d")

    # Calculate the date one month before
    from_date = (date_obj - timedelta(days=30)).strftime("%Y-%m-%d")

    # Keep the original target date as 'to'
    to_date = date_obj.strftime("%Y-%m-%d")

    # Now construct your payload
    payload = {
        "input": {
            "bounds": {
                "bbox": bbox
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{from_date}T00:00:00Z",
                        "to": f"{to_date}T23:59:59Z"
                    },
                    "maxCloudCoverage": 100
                }
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/jpeg"}  # JPEG format
            }]
        },
        "evalscript": evalscript,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    process_url = "https://services.sentinel-hub.com/api/v1/process"
    result = requests.post(process_url, json=payload, headers=headers)

    if result.status_code == 200:
        try:
            print("Received Image Data")
            with open(file_name, "wb") as file:
                file.write(result.content)
            return f"Image saved as {file_name}"
        except requests.exceptions.JSONDecodeError:
            return f"Error: Could not decode JSON from response. Raw response: {result.text}"
    else:
        return f"Error: {result.status_code} - {result.text}"

# Example usage
latitude = 19.291128
longitude = 73.086392
date = "2025-04-21"
layer = "vegetation"  # Use TRUE_COLOR for RGB with scaling
file_name = "satellite_image(vegetation).jpg"  # Specify the local filename to save the image

result_message = get_satellite_image_and_save(latitude, longitude, date, layer.upper(), file_name)
print(result_message)
