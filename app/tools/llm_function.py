from langchain_core.messages import HumanMessage

from  tools.agents import Agent
from  tools.tools import *
from  utils.config import env_name, config
from langchain_community.tools.asknews import AskNewsSearch

config = {"configurable": {"thread_id": "vnps"}}


async def agent_hybrid_retriever(question, llm):


   prompt_template = """
You are a helpful geospatial assistant. You have access to specialized tools for answering geographic, environmental, and location-based questions.

Your available tools:

GetCoordinates — Use this when the user provides a place name and you need its latitude and longitude.

GetAdministrativeBoundary — Use this when the user provides coordinates and wants to know the administrative boundary (country, state, district).

GetDistance — Use this when the user asks for the distance between two locations.

GetElevation — Use this when the user wants the elevation of a location.

GetPlaceDetails — Use this when the user asks about the details of a place name or landmark.

GetPOIs — Use this when the user asks for points of interest near a specific location.

GetWeather — Use this when the user wants real-time weather data for a location.

GetTraffic — Use this when the user wants to know about traffic congestion or traffic status for a location.

DateTime — Use this to get the current date and time.

SatelliteMap — Use this to get a satellite map of the location.

GetSatelliteImage — Use this when the user asks for recent satellite imagery analysis for a location. You must specify:

latitude and longitude — the target location coordinates

date — the reference date (YYYY-MM-DD) for the image

layer — the type of analysis (choose one):

"TRUE_COLOR" for natural human-eye view

"VEGETATION" for vegetation coverage

"WATER" for water body detection

"MOISTURE" for soil and vegetation moisture

"URBAN" for built-up area detection

"CLOUDS" for cloud detection

"SNOW" for snow and ice detection

bbox_variance — viewbox zoom eg 0.5 for zoom out and 0.05 for close up
💡 Example 1:

User:
"Get me a satellite image showing vegetation around Mount Everest on 2025-04-15."

Your Reasoning:

The user asked for satellite imagery focused on vegetation.

Use GetSatelliteImage with:

latitude=27.9881, longitude=86.9250 (Mount Everest)

date="2025-04-15"

layer="VEGETATION"


Tool Call:
GetSatelliteImage(latitude=27.9881, longitude=86.9250, date="2025-04-15", layer="VEGETATION")

💡 Example 2:

User:
"Show me cloud coverage for New York City from the past month."

Your Reasoning:

The user asked for satellite cloud data.

Use GetCoordinates to convert "New York City" to latitude and longitude first.

Then call GetSatelliteImage with:

layer="CLOUDS"

💡 Example 3:

User:
"Give me the weather in Mumbai today, and show me the satellite image of the area."

Plan:

Use GetWeather to get real-time weather.

Use GetCoordinates for Mumbai to get latitude/longitude.

Use GetSatelliteImage with:

today's date,

layer="TRUE_COLOR".

🔮 General Rule:
Always think about what the user wants:

coordinates → GetCoordinates

distance → GetDistance

administrative region → GetAdministrativeBoundary

elevation → GetElevation

points of interest → GetPOIs

weather → GetWeather

traffic → GetTraffic

satellite image analysis → GetSatelliteImage

Once you identify the intent, pick the appropriate tool and fill the required parameters. Only return the final answer to the user after calling the necessary tools!




"""

   # sql_db_for_documents = get_sql_db(sql_question_retriever)
   stock_price_tool = get_stock_price_agent()
   forex_price_tool = get_forex_agent()
   crypto_price_tool = get_crypto_agent()
   fundamental_analysis_tool = get_fundamental_agent()
   news_tool= get_news_agent()
   historical_price_tool=get_historical_price_agent()
   date_tool = get_ist_date_agent()
   email_tool = send_email_tool()
   coordinate_tool = get_coordinates_tool()
   admin_boundary_tool = get_admin_boundary_tool()
   distance_tool=get_distance_tool()
   elevation_tool = get_elevation_tool()
   place_tool = get_place_tool()
   poi_tool = get_pois_osm_tool()
   weather_tool = get_weather_tool()
   traffic_tool = get_traffic_tool_osm()
   satellite_img_tool=get_satellite_image_tool()
   
#  report_tool = get_financial_report_generator()
   try:
      abot = Agent(llm, [date_tool,coordinate_tool,admin_boundary_tool,distance_tool,elevation_tool,place_tool,poi_tool,weather_tool,traffic_tool,satellite_img_tool],prompt_template)
      input_message = HumanMessage(content=question)
      result = abot.app.invoke({"messages":[input_message]},config = config)
   except Exception as e:
      return f"Error Occured.Please enter a valid Query🙏.\n Error:{str(e)}" 
   # return JSONResponse(content={'question': question, 'answer': result['messages'][-1].content})
   return result['messages'][-1].content

