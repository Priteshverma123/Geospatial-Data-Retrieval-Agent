from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain.tools.base import StructuredTool
from langchain.tools.retriever import create_retriever_tool
from pydantic import BaseModel, Field
from langsmith import traceable
from  tools.tool_helpers import *
from typing import Optional, Dict, List
from pydantic import BaseModel, EmailStr, Field
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@traceable
def get_retriever_tool(retriever):
    retriever_tool = create_retriever_tool(
        retriever,
        "document_search",
        (
            "Retrieve relevant contract information. Use this tool only once per question, "
            "unless instructed otherwise."
        ),
    )
    return retriever_tool


@traceable
def get_knowledge_graph_for_documents(hybrid_ensemble_retriever):
    return StructuredTool(
        args_schema=ArgsSchema,
        func=hybrid_ensemble_retriever,
        name="knowledge_graph_for_documents",
        description="Use this tool to extract information from documents which are embedded in the vector database.",
    )

@traceable
def get_multimodal_for_documents(multimodal_retriever):
    return StructuredTool(
        args_schema=ArgsSchema,
        func=multimodal_retriever,
        name="multimodal_for_documents",
        description="Use this tool to extract information from documents which are embedded multimodal vector database.",
    )


@traceable
def get_stock_price_agent():
    return StructuredTool(
        args_schema=StockQuerySchema,
        func=fetch_stock_price,
        name="stock_price_agent",
        description="Fetches real-time and historical stock prices for a given symbol."
    )
    
@traceable
def get_forex_agent():
    return StructuredTool(
        args_schema=ForexQuerySchema,
        func=fetch_forex_data,
        name="forex_trading_agent",
        description="Retrieves real-time and historical exchange rates for currency pairs."
    )
    
@traceable    
def get_crypto_agent():
    return StructuredTool(
        args_schema=CryptoQuerySchema,
        func=fetch_crypto_data,
        name="crypto_market_agent",
        description="Tracks cryptocurrency price movements and trends in real-time and historically."
    )

@traceable
def get_fundamental_agent():
    return StructuredTool(
        args_schema=FundamentalQuerySchema,
        func=fetch_fundamental_data,
        name="fundamental_data_agent",
        description="Fetches company financial statements such as Income Statement, Balance Sheet, and Cash Flow."
    )
@traceable
def get_news_agent():
    return StructuredTool(
        args_schema=NewsQuerySchema,
        func=fetch_news_newsapi,
        name="news_agent",
        description="Fetches the latest financial news using NewsAPI (open-source)."
    )

def get_financial_report_generator():
    return StructuredTool(
        args_schema=FinancialDataSchema,
        func=parse_and_generate_financial_report,
        name="financial_report_generator",
        description="Generates a well-detailed financial report from stock, fundamental, forex, crypto, and news data."
    )

def get_historical_price_agent():
    return StructuredTool(
        args_schema=HistoricalPriceSchema,
        func=fetch_historical_price_data,
        name="historical_price_agent",
        description="Fetches historical price data for stocks, forex, or crypto over a specified period."
    )

def get_ist_date_agent():
    return StructuredTool(
        args_schema=DateQuerySchema,
        func=fetch_ist_date,
        name="ist_date_agent",
        description="Fetches the current date in Indian Standard Time (IST)."
    )

    
def create_agent_executor(llm, tools, prompt):
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor
    
class PlaceNameInput(BaseModel):
    place_name: str = Field(
        description="The Place name to be converted to Coordinates")
    

def get_coordinates_tool() :
    return StructuredTool(
    func=get_coordinates,
    name="GetCoordinatesFromPlace",
    description="Converts a place name into latitude and longitude using OpenStreetMap data.",
    args_schema=PlaceNameInput
)


class CoordinatesInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")

def get_place_tool() : 
    return StructuredTool(
    func=get_place_from_coordinates,
    name="GetPlaceFromCoordinates",
    description="Converts latitude and longitude into a human-readable place name using OpenStreetMap data.",
    args_schema=CoordinatesInput
)

class DistanceInput(BaseModel):
    lat1: float= Field(
        description="Latitude of the First Coordinate")
    lon1: float= Field(
        description="Longitude of the First Coordinate")
    lat2: float= Field(
        description="Latitude of the Second Coordinate")
    lon2: float= Field(
        description="Longitude of the Second Coordinate")

def get_distance_tool():
    return StructuredTool(
    func=get_distance,
    name="GetDistanceBetweenPoints",
    description="Calculates the Haversine distance between two sets of coordinates in kilometers.",
    args_schema=DistanceInput
)

class POIInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")
    radius: int = Field(
        description="Search Radius in meters for POIs") # Radius in meters

def get_pois_osm_tool() : 
    return StructuredTool(
    func=get_nearby_pois_osm,
    name="GetNearbyPointsOfInterest",
    description="Finds nearby points of interest like hospitals, restaurants, and more using the OpenStreetMap Overpass API.",
    args_schema=POIInput
)

class ElevationInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")


def get_elevation_tool() : 
    return StructuredTool(
    func=get_elevation,
    name="GetElevation",
    description="Fetches the elevation (altitude) of a given location using the Open Elevation API.",
    args_schema=ElevationInput
)

class WeatherInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")



def get_weather_tool() : 
    return StructuredTool(
    func=get_weather_forecast,
    name="GetWeatherForecast",
    description="Fetches the weather forecast for a given location using the OpenWeatherMap API.",
    args_schema=WeatherInput
)

class TrafficInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")

    

def get_traffic_tool_osm() :
    return StructuredTool(
    func=get_traffic_data_osm,
    name="GetTrafficData",
    description="Fetches traffic data for a given location using OpenStreetMap-based traffic data sources.",
    args_schema=TrafficInput
)

class AdminBoundaryInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")


def get_admin_boundary_tool(): 
    return StructuredTool(
    func=get_admin_boundary,
    name="GetAdministrativeBoundary",
    description="Fetches administrative boundaries like district, state, or country for a given latitude and longitude using OpenCage Geocoder API.",
    args_schema=AdminBoundaryInput
)

class SatelliteImageInput(BaseModel):
    latitude: float= Field(
        description="Latitude of the Given Coordinate")
    longitude: float= Field(
        description="Longitude of the Given Coordinate")
    date: str= Field(
        description="Todays date time")  # Format: YYYY-MM-DD
    layer: str = Field(
        description="""The `layer` parameter defines the type of satellite analysis you want to perform.  
It selects the appropriate band combination via an evalscript to highlight specific features.

Available options:

1. "TRUE_COLOR" — Natural Color Composite  
   Bands: B04 (Red), B03 (Green), B02 (Blue)  
   Output: Realistic human-eye-like image.

2. "VEGETATION" — Vegetation Highlight (NDVI-like)  
   Bands: B08 (NIR), B04 (Red)  
   Output: Vegetation areas in bright green. Non-vegetation in dark or neutral colors.

3. "WATER" — Water Detection  
   Bands: B03 (Green), B08 (NIR)  
   Output: Water bodies appear blue, land appears darker.

4. "MOISTURE" — Soil and Vegetation Moisture  
   Bands: B11 (SWIR), B08 (NIR)  
   Output: High moisture areas in brighter tones, dry areas are darker.

5. "URBAN" — Urban Area Detection  
   Bands: B12 (SWIR2), B11 (SWIR1), B04 (Red)  
   Output: Urban objects appear bright and distinct, vegetation is dark.

6. "CLOUDS" — Cloud Detection  
   Bands: B01 (Aerosol), B02 (Blue), B04 (Red), B10 (Cirrus)  
   Output: Clouds are bright; clear-sky areas are dark.

7. "SNOW" — Snow and Ice Detection  
   Bands: B03 (Green), B11 (SWIR)  
   Output: Snow and ice appear white or cyan; land and water appear darker.

Use this parameter to select the focus of your satellite image analysis.
""") 
    bbox_variance: float= Field(
        description="this will define the zoom eg 0.5 will +- from lat and long to get a viewbox try not to exceed 0.05 tho image gets pixelated")
    
def get_satellite_image_tool():
    return StructuredTool(
    func=get_satellite_image_and_save,
    name="GetSatelliteImage",
    description="Fetches a true-color satellite image for given latitude, longitude and date using NASA GIBS.",
    args_schema=SatelliteImageInput
)
################################# Here Lie The Input Model Args ########################
class ArgsSchema(BaseModel):
    question: str = Field()


class StockQuerySchema(BaseModel):
    symbol: str = Field(description="Stock symbol (e.g., AAPL, TSLA, GOOG)")
    timeframe: str = Field(
        description="Timeframe for stock data (daily, weekly, monthly). Default is 'daily'.",
        default="daily"
    )
    
class TAQuerySchema(BaseModel):
    symbol: str = Field(description="Stock symbol (e.g., AAPL, TSLA, GOOG)")
    indicators: str = Field(
        description="Comma-separated list of technical indicators (SMA, EMA, RSI, MACD, BBANDS). Default is all.",
        default="SMA,EMA,RSI,MACD,BBANDS"
    )    
    
class ForexQuerySchema(BaseModel):
    base_currency: str = Field(description="Base currency (e.g., USD, EUR, GBP)")
    target_currency: str = Field(description="Target currency (e.g., JPY, INR, CAD)")
    timeframe: str = Field(
        description="Timeframe for historical data (intraday, daily, weekly, monthly). Default is 'daily'.",
        default="daily"
    )    
    
class CryptoQuerySchema(BaseModel):
    crypto_symbol: str = Field(description="Cryptocurrency symbol (e.g., BTC, ETH, SOL)")
    fiat_currency: str = Field(description="Fiat currency (e.g., USD, EUR, USDT)")
    timeframe: str = Field(
        description="Timeframe for historical data (intraday, daily, weekly, monthly). Default is 'daily'.",
        default="daily"
    )
    
class FundamentalQuerySchema(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol (e.g., 'AAPL' for Apple, 'TSLA' for Tesla)."
    )
    report_type: str = Field(
        description="Type of fundamental data. Options: 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW'."
    )

class NewsQuerySchema(BaseModel):
    query: str = Field(
        description="Search query for news (e.g., 'Tesla stock', 'Bitcoin price', 'Inflation rate')."
    )
    num_results: int = Field(default=5, description="Number of articles to fetch (default is 5).")

class FinancialDataSchema(BaseModel):
    stock_data: Optional[Dict] = Field(default=None, description="Stock price data in dictionary format.")
    fundamental_data: Optional[Dict] = Field(default=None, description="Fundamental analysis data.")
    forex_data: Optional[Dict] = Field(default=None, description="Forex data in dictionary format.")
    crypto_data: Optional[Dict] = Field(default=None, description="Cryptocurrency data in dictionary format.")
    news_data: Optional[List[Dict[str, str]]] = Field(default=None, description="Financial news articles list.")

class HistoricalPriceSchema(BaseModel):
    ticker: str = Field(description="Ticker symbol (e.g., 'AAPL' for Apple, 'BTC-USD' for Bitcoin, 'EURUSD=X' for Forex).")
    start_date: Optional[str] = Field(default=None, description="Start date for historical data in 'YYYY-MM-DD' format.")
    end_date: Optional[str] = Field(default=None, description="End date for historical data in 'YYYY-MM-DD' format.")
    interval: str = Field(default="1d", description="Data interval. Options: '1m', '5m', '1h', '1d', '1wk', '1mo'.")

class DateQuerySchema(BaseModel):
    """No input required as it defaults to IST."""
    pass

# Hardcoded sender credentials
SENDER_EMAIL = "harshvardhan.surve@gmail.com"
SENDER_PASSWORD = "giey oxed xaju udfn"

# Define input schema with descriptions
class SendEmailSchema(BaseModel):
    recipient_email: EmailStr = Field(description="The recipient's email address.")
    subject: str = Field(description="The subject of the email.")
    body: str = Field(description="The main content of the email.")
    cc_email: Optional[EmailStr] = Field(default=None, description="Optional CC email address.")
    bcc_email: Optional[EmailStr] = Field(default=None, description="Optional BCC email address.")

# Function to send an email
def send_email(recipient_email: str, subject: str, body: str, cc_email: Optional[str] = None, bcc_email: Optional[str] = None) -> str:
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject

        if cc_email:
            msg["Cc"] = cc_email  # Add CC
        if bcc_email:
            msg["Bcc"] = bcc_email  # Add BCC

        msg.attach(MIMEText(body, "plain"))

        # Prepare recipient list
        recipient_list = [recipient_email]
        if cc_email:
            recipient_list.append(cc_email)
        if bcc_email:
            recipient_list.append(bcc_email)

        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_list, msg.as_string())
        server.quit()
        
        return f"Email sent successfully to {recipient_email}!"
    
    except Exception as e:
        return f"Error: {e}"

# Create a structured tool for LangChain
def send_email_tool():
    return StructuredTool(
    name="send_email",
    description="Sends an email using SMTP. Requires recipient email, subject, and body. Optionally supports CC and BCC.",
    func=send_email,
    args_schema=SendEmailSchema,
)