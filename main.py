from fastapi import FastAPI
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from fastapi.responses import FileResponse
from dotenv import dotenv_values

config = dotenv_values(".env")

app = FastAPI()

def get_forecast_daily_description(data):
    date = data["date"]
    max_temp = data["day"]["maxtemp_c"]
    min_temp = data["day"]["mintemp_c"]
    daily_chance_of_rain = f'{data["day"]["daily_chance_of_rain"]} %'
    return {
        "date":date,
        "max":max_temp,
        "min":min_temp,
        "chance_of_rain":daily_chance_of_rain
    }    

def get_astro_daily_description(data):
    date=data["date"]
    sunrise = data["astro"]["sunrise"]
    sunset = data["astro"]["sunset"]
    return {
        "date":date,
        "sunrise":sunrise,
        "sunset":sunset
    }    

def get_weather_data(days:int, location:str, api_key:str):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days={days}&aqi=no&alerts=no"
    weather_data = requests.get(url).json()    
    
    image_urls = ["https:"+i["day"]["condition"]["icon"] for i in weather_data["forecast"]["forecastday"]]
    descriptions = [get_forecast_daily_description(i) for i in weather_data["forecast"]["forecastday"]]
    astro_descriptions = [get_astro_daily_description(i) for i in weather_data["forecast"]["forecastday"]]
    images = [Image.open(BytesIO(requests.get(i).content)) for i in image_urls]
    min_shape = sorted( [(np.sum(i.size), i.size ) for i in images])[0][1]
    imgs_comb = np.hstack([i.resize(min_shape) for i in images])

    imgs_comb = Image.fromarray( imgs_comb)
    icons_location = config.get("WEATHER_ICONS_LOCATION")
    imgs_comb.save(icons_location,bitmap_format='png')    
    return {"astros":astro_descriptions,"weather":descriptions}

@app.get("/weather/getcurrentimg")
async def get_weather_icons():
    fn = config.get("WEATHER_ICONS_LOCATION")
    return FileResponse(fn)


@app.get("/weather/default")
def get_weather():        
    return get_weather_data(config.get("DEF_DAYS_AHEAD"),config.get("LONG_LAT"),config.get("WEATHER_API_KEY"))

@app.get("/weather/{longlat}")
def get_weather(longlat:str):    
    api_key = config.get("WEATHER_API_KEY")
    return get_weather_icons(config.get("DEF_DAYS_AHEAD"),longlat,api_key)