import yfinance as yf
import pandas_ta as ta
from forex_python.converter import CurrencyRates
import pandas as pd
from langchain_community.tools.asknews import AskNewsSearch
import requests , math
from typing import Optional
from datetime import datetime
from pytz import timezone
from utils.config import config, load_env_variables
env_name = load_env_variables()

NEWS_API_KEY = config[env_name].NEWS_API_KEY 
NEWS_API_URL = config[env_name].NEWS_API_URL
CLIENT_ID = config[env_name].CLIENT_ID 
CLIENT_SECRET = config[env_name].CLIENT_SECRET 


def fetch_stock_price(symbol: str, timeframe: str = "daily"):
    """Fetch real-time or historical stock prices using Yahoo Finance."""
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")  # Fetch last 1-month data

    if data.empty:
        return f"Stock symbol '{symbol}' not found."

    latest_data = data.iloc[-1]  # Most recent row

    response = {
        "symbol": symbol,
        "latest_price": latest_data["Close"],
        "open": latest_data["Open"],
        "high": latest_data["High"],
        "low": latest_data["Low"],
        "volume": latest_data["Volume"]
    }

    # Handle different timeframes
    if timeframe == "weekly":
        response["weekly_avg"] = data["Close"].resample('W').mean().iloc[-1]
    elif timeframe == "monthly":
        response["monthly_avg"] = data["Close"].resample('M').mean().iloc[-1]

    return response


def fetch_technical_indicators(symbol: str, indicators: str = "SMA,EMA,RSI,MACD,BBANDS"):
    """Fetch technical indicators using Yahoo Finance & pandas_ta."""
    stock = yf.Ticker(symbol)
    data = stock.history(period="6mo")  # Fetch last 6 months of data

    if data.empty:
        return f"Stock symbol '{symbol}' not found."

    result = {"symbol": symbol}

    # Compute indicators based on user input
    indicator_list = indicators.split(",")

    if "SMA" in indicator_list:
        data["SMA_50"] = ta.sma(data["Close"], length=50)
        data["SMA_200"] = ta.sma(data["Close"], length=200)
        result["SMA"] = {"50-day": data["SMA_50"].iloc[-1], "200-day": data["SMA_200"].iloc[-1]}

    if "EMA" in indicator_list:
        data["EMA_50"] = ta.ema(data["Close"], length=50)
        data["EMA_200"] = ta.ema(data["Close"], length=200)
        result["EMA"] = {"50-day": data["EMA_50"].iloc[-1], "200-day": data["EMA_200"].iloc[-1]}

    if "RSI" in indicator_list:
        data["RSI"] = ta.rsi(data["Close"], length=14)
        result["RSI"] = data["RSI"].iloc[-1]

    if "MACD" in indicator_list:
        macd = ta.macd(data["Close"], fast=12, slow=26, signal=9)
        result["MACD"] = {
            "MACD": macd["MACD_12_26_9"].iloc[-1],
            "Signal": macd["MACDs_12_26_9"].iloc[-1],
            "Histogram": macd["MACDh_12_26_9"].iloc[-1],
        }

    if "BBANDS" in indicator_list:
        bbands = ta.bbands(data["Close"], length=20)
        result["Bollinger Bands"] = {
            "Upper Band": bbands["BBU_20_2.0"].iloc[-1],
            "Lower Band": bbands["BBL_20_2.0"].iloc[-1],
            "Middle Band": bbands["BBM_20_2.0"].iloc[-1],
        }

    return result


def fetch_forex_data(base_currency: str, target_currency: str, timeframe: str = "daily"):
    """Fetch real-time and historical forex exchange rates."""
    
    # Real-time exchange rate using forex-python
    currency_rates = CurrencyRates()
    try:
        real_time_rate = currency_rates.get_rate(base_currency, target_currency)
    except:
        return f"Could not fetch real-time exchange rate for {base_currency}/{target_currency}."

    # Historical data using Yahoo Finance
    forex_pair = f"{base_currency}{target_currency}=X"
    forex_data = yf.Ticker(forex_pair)

    if timeframe == "intraday":
        data = forex_data.history(period="7d", interval="1h")  # Last 7 days, hourly data
    elif timeframe == "weekly":
        data = forex_data.history(period="6mo", interval="1wk")  # Last 6 months, weekly data
    elif timeframe == "monthly":
        data = forex_data.history(period="2y", interval="1mo")  # Last 2 years, monthly data
    else:
        data = forex_data.history(period="1y", interval="1d")  # Default: Last 1 year, daily data

    if data.empty:
        return f"Could not fetch {timeframe} historical data for {base_currency}/{target_currency}."

    last_close = data["Close"].iloc[-1]
    history_summary = {
        "Real-Time Rate": real_time_rate,
        "Last Close Price": last_close,
        "Timeframe": timeframe,
        "Historical Data (last 5 records)": data["Close"].tail(5).to_dict()
    }

    return history_summary


def fetch_crypto_data(crypto_symbol: str, fiat_currency: str, timeframe: str = "daily"):
    """Fetch real-time and historical crypto price data."""

    # Format crypto ticker for Yahoo Finance (e.g., BTC-USD)
    crypto_pair = f"{crypto_symbol}-{fiat_currency}"
    crypto_data = yf.Ticker(crypto_pair)

    try:
        # Get real-time price
        real_time_price = crypto_data.history(period="1d")["Close"].iloc[-1]
    except:
        return f"Could not fetch real-time price for {crypto_symbol}/{fiat_currency}."

    # Fetch historical data based on timeframe
    if timeframe == "intraday":
        data = crypto_data.history(period="7d", interval="1h")  # Last 7 days, hourly data
    elif timeframe == "weekly":
        data = crypto_data.history(period="6mo", interval="1wk")  # Last 6 months, weekly data
    elif timeframe == "monthly":
        data = crypto_data.history(period="2y", interval="1mo")  # Last 2 years, monthly data
    else:
        data = crypto_data.history(period="1y", interval="1d")  # Default: Last 1 year, daily data

    if data.empty:
        return f"Could not fetch {timeframe} historical data for {crypto_symbol}/{fiat_currency}."

    last_close = data["Close"].iloc[-1]
    history_summary = {
        "Real-Time Price": real_time_price,
        "Last Close Price": last_close,
        "Timeframe": timeframe,
        "Historical Data (last 5 records)": data["Close"].tail(5).to_dict()
    }

    return history_summary

def fetch_fundamental_data(ticker: str, report_type: str):
    """Retrieve company financial statements from Yahoo Finance."""
    
    stock = yf.Ticker(ticker)
    
    if report_type == "INCOME_STATEMENT":
        data = stock.financials
    elif report_type == "BALANCE_SHEET":
        data = stock.balance_sheet
    elif report_type == "CASH_FLOW":
        data = stock.cashflow
    else:
        return "Invalid report type. Choose from: INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW."
    
    # Convert data to dictionary format
    if data.empty:
        return f"No data found for {ticker}."

    latest_data = data.iloc[:, :5].to_dict()  # Latest 5 columns (quarters or years)

    return {
        "Ticker": ticker,
        "Report Type": report_type,
        "Latest Data": latest_data
    }
    

def fetch_news_asknews(query: str, num_results: int = 5):
    """Fetch latest news using LangChain's AskNews tool."""
    news_tool = AskNewsSearch()

    results = news_tool.run(query)
    
    if not results:
        return {"message": f"No news found for '{query}'."}

    # Extract top 'num_results' articles
    news_summary = results[:num_results]

    return {
        "Query": query,
        "Latest News": news_summary
    }
    
    
def fetch_news_newsapi(query: str, num_results: int = 5):
    """Fetch latest news using NewsAPI (open-source)."""
    
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "pageSize": num_results
    }
    
    response = requests.get(NEWS_API_URL, params=params)
    data = response.json()
    
    if data.get("status") != "ok":
        return {"error": "Failed to fetch news.", "details": data}

    articles = data.get("articles", [])
    
    if not articles:
        return {"message": f"No news found for '{query}'."}

    news_summary = [{"title": article["title"], "url": article["url"]} for article in articles[:num_results]]
    
    return {
        "Query": query,
        "Latest News": news_summary
    }
    
def parse_and_generate_financial_report(stock_data=None, fundamental_data=None, forex_data=None, crypto_data=None, news_data=None):
    """Parse and present financial data in a detailed report format."""
    
    report = "📝 **Detailed Financial Report**\n"
    report += "=" * 50 + "\n"

    # Stock Price Section
    if stock_data:
        report += "📈 **Stock Price Data:**\n"
        for key, value in stock_data.items():
            report += f"{key}: {value}\n"
        report += "-" * 50 + "\n"

    # Fundamental Analysis Section
    if fundamental_data:
        report += "📊 **Fundamental Analysis:**\n"
        for key, value in fundamental_data.get("Latest Data", {}).items():
            report += f"{key:<30}: {value}\n"
        report += "-" * 50 + "\n"

    # Forex Data Section
    if forex_data:
        report += "💱 **Forex Data:**\n"
        for currency_pair, value in forex_data.items():
            report += f"{currency_pair}: {value}\n"
        report += "-" * 50 + "\n"

    # Cryptocurrency Data Section
    if crypto_data:
        report += "💰 **Cryptocurrency Data:**\n"
        for crypto, value in crypto_data.items():
            report += f"{crypto}: {value}\n"
        report += "-" * 50 + "\n"
    
    # Financial News Section
    if news_data:
        report += "📰 **Financial News:**\n"
        for article in news_data:
            report += f"- {article.get('title', 'No Title')} ({article.get('source', 'Unknown Source')})\n"
        report += "-" * 50 + "\n"
    
    if not any([stock_data, fundamental_data, forex_data, crypto_data, news_data]):
        report += "No data available for the requested report."

    return report



def fetch_historical_price_data(ticker: str, start_date: Optional[str], end_date: Optional[str], interval: str):
    """Fetch historical price data for stocks, crypto, or forex."""
    stock = yf.Ticker(ticker)
    
    # Fetch data within the specified date range and interval
    try:
        data = stock.history(start=start_date, end=end_date, interval=interval)
    except Exception as e:
        return {"error": str(e)}
    
    if data.empty:
        return f"No historical price data found for {ticker} between {start_date} and {end_date}."
    
    # Format report for the latest records
    report = f"📈 **Historical Price Data for {ticker}**\n"
    report += "=" * 50 + "\n"
    report += f"Interval: {interval}\n"
    report += "-" * 50 + "\n"
    
    # Show the latest 5 data points
    latest_data = data.tail(5).reset_index()
    for i, row in latest_data.iterrows():
        report += f"{row['Date']}: Open={row['Open']:.2f}, High={row['High']:.2f}, Low={row['Low']:.2f}, Close={row['Close']:.2f}\n"
    
    return report

def fetch_ist_date():
    """Fetch the current date in Indian Standard Time (IST)."""
    ist = timezone("Asia/Kolkata")
    current_date = datetime.now(ist).strftime("%Y-%m-%d")
    return {"timezone": "Indian Standard Time (IST)", "current_date": current_date}

def get_coordinates(place_name: str) -> str:
    """Converts a place name into latitude and longitude using OpenStreetMap's Nominatim API."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "Geospatial-Agent"}
    response = requests.get(url, params=params, headers=headers).json()

    if response:
        lat = response[0]['lat']
        lon = response[0]['lon']
        return f"Coordinates for '{place_name}' are: Latitude {lat}, Longitude {lon}."
    return f"Could not find coordinates for '{place_name}'."

def get_place_from_coordinates(latitude: float, longitude: float) -> str:
    """Converts latitude and longitude into a human-readable place name using OpenStreetMap's Nominatim API."""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": latitude, "lon": longitude, "format": "json", "addressdetails": 1}
    headers = {"User-Agent": "Geospatial-Agent"}
    response = requests.get(url, params=params, headers=headers).json()

    if 'address' in response:
        place_name = response['address'].get('road', 'Unknown road') + ", " + response['address'].get('city', 'Unknown city')
        country = response['address'].get('country', 'Unknown country')
        return f"The location at ({latitude}, {longitude}) is: {place_name}, {country}."
    return f"Could not determine the place for coordinates ({latitude}, {longitude})."


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Calculate the Haversine distance between two coordinates."""
    R = 6371  # Radius of the Earth in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # Distance in kilometers
    return distance

def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Calculates the distance between two points using the Haversine formula."""
    distance = haversine(lat1, lon1, lat2, lon2)
    return f"The distance between ({lat1}, {lon1}) and ({lat2}, {lon2}) is {distance:.2f} kilometers."

def get_nearby_pois_osm(latitude: float, longitude: float, radius: int) -> str:
    """Finds nearby points of interest like hospitals, restaurants, etc., using the OpenStreetMap Overpass API."""
    url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node(around:{radius},{latitude},{longitude})["amenity"];
      way(around:{radius},{latitude},{longitude})["amenity"];
      relation(around:{radius},{latitude},{longitude})["amenity"];
    );
    out body;
    """
    params = {
        "data": query
    }
    response = requests.get(url, params=params).json()

    if 'elements' in response:
        pois = [element.get('tags', {}).get('name', 'Unnamed place') for element in response['elements']]
        if pois:
            return f"Nearby points of interest: {', '.join(pois)}"
        else:
            return "No nearby points of interest found."
    return "Error retrieving points of interest."

def get_elevation(latitude: float, longitude: float) -> str:
    """Fetches the elevation (altitude) for a given latitude and longitude using the Open Elevation API."""
    url = "https://api.open-elevation.com/api/v1/lookup"
    params = {"locations": f"{latitude},{longitude}"}
    response = requests.get(url, params=params).json()

    if 'results' in response and len(response['results']) > 0:
        elevation = response['results'][0]['elevation']
        return f"The elevation at ({latitude}, {longitude}) is {elevation} meters."
    return f"Could not determine the elevation for coordinates ({latitude}, {longitude})."

def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Fetches the weather forecast for a given latitude and longitude using the OpenWeatherMap API."""
    api_key = "5563df9b8a3d721191689f5e4b997d5b"  # Replace with your actual API key
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric"  # Celsius temperature
    }
    response = requests.get(url, params=params).json()

    if response.get('weather'):
        weather_desc = response['weather'][0]['description']
        temp = response['main']['temp']
        return f"The current weather at ({latitude}, {longitude}) is {weather_desc} with a temperature of {temp}°C."
    return "Error retrieving weather data."

def get_traffic_data_osm(latitude: float, longitude: float) -> str:
    """Fetches real-time traffic data for a given location using TomTom Traffic API."""
    api_key = "EWc6tgPhGE9aTgGoiG7UTXXn9FXPOtJt"  # Replace with your actual TomTom key
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
    params = {
        "point": f"{latitude},{longitude}",
        "key": api_key
    }
    response = requests.get(url, params=params).json()

    try:
        congestion = response["flowSegmentData"]["currentSpeed"]
        freeFlow = response["flowSegmentData"]["freeFlowSpeed"]
        jamFactor = response["flowSegmentData"]["confidence"]
        return (f"Traffic Status at ({latitude}, {longitude}):\n"
                f"- Current Speed: {congestion} km/h\n"
                f"- Free Flow Speed: {freeFlow} km/h\n"
                f"- Confidence: {jamFactor}")
    except KeyError:
        return "Unable to retrieve traffic data. Check coordinates or API limits."

def get_admin_boundary(latitude: float, longitude: float) -> str:
    """Fetches administrative boundary (district, state, country) for a given latitude and longitude using OpenCage Geocoder API."""
    api_key = "e5ad71108aef407a89d5168bbab7d234"  # Replace with your actual API key
    url = f"https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": f"{latitude},{longitude}",
        "key": api_key
    }
    response = requests.get(url, params=params).json()

    if 'results' in response and len(response['results']) > 0:
        components = response['results'][0]['components']
        country = components.get('country', 'Unknown')
        state = components.get('state', 'Unknown')
        county = components.get('county', 'Unknown')
        return f"The administrative boundaries for ({latitude}, {longitude}) are: Country - {country}, State - {state}, County - {county}."
    return "Error retrieving administrative boundaries."
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
        let r = sample.B04 * 2.5;
        let g = sample.B03 * 2.5;
        let b = sample.B02 * 2.5;

        return [
            Math.min(1, r),
            Math.min(1, g),
            Math.min(1, b)
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




def get_satellite_image_and_save(latitude: float, longitude: float, date: str, layer: str, bbox_variance:float) -> str:
 # Replace this with your client secret

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
    bbox = [longitude - bbox_variance, latitude - bbox_variance, longitude + bbox_variance, latitude + bbox_variance]  # Increased bounding box
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
                    "maxCloudCoverage": 20
                }
            }]
        },
        "output": {
            "width": 1024,
            "height": 1024,
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
    file_name="satellite_image.jpg"
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