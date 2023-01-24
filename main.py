from fastapi import FastAPI, Response
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
    description = data["day"]["condition"]["text"]
    daily_chance_of_rain = f'{int(data["day"]["daily_chance_of_rain"])} %'
    humidity=f'{int(data["day"]["avghumidity"])} %'
    return {
        "date":date,
        "max":max_temp,
        "min":min_temp,
        "description":description,
        "humidity":humidity,
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

def get_concat_h_multi_resize(im_list, resample=Image.BICUBIC):
    min_height = min(im.height for im in im_list)
    im_list_resize = [im.resize((int(im.width * min_height / im.height), min_height),resample=resample) for im in im_list]
    total_width = sum(im.width for im in im_list_resize)
    dst = Image.new('RGB', (total_width, min_height))
    pos_x = 0
    for im in im_list_resize:
        dst.paste(im, (pos_x, 0))
        pos_x += im.width
    return dst
def get_weather_data(days:int, location:str, api_key:str):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days={days}&aqi=no&alerts=no"
    print(url)
    weather_data = requests.get(url).json()     
    # print(weather_data["forecast"]["forecastday"])
    image_urls = ["https:"+i["day"]["condition"]["icon"] for i in weather_data["forecast"]["forecastday"]]
    # print(image_urls)
    descriptions = [get_forecast_daily_description(i) for i in weather_data["forecast"]["forecastday"]]
    print("descriptions", descriptions)
    astro_descriptions = [get_astro_daily_description(i) for i in weather_data["forecast"]["forecastday"]]
    images = [Image.open(BytesIO(requests.get(i).content)) for i in image_urls]
    print("images: ", len(images))
    #min_shape = sorted([(np.sum(i.size), i.size ) for i in images])[0][1] 
    #resized = [i.resize(min_shape) for i in images]
    #print("resized ",resized)
    #ic = np.hstack(images)
    #print(ic)    
    icons_location = config.get("WEATHER_ICONS_LOCATION")
    print(icons_location)
    combined_images = get_concat_h_multi_resize(images)
    combined_images.save(icons_location,bitmap_format='png')    
    print("Images saved")
    return {"astros":astro_descriptions,"weather":descriptions}

@app.get("/weather/getcurrentimg")
def get_weather_icons(response:Response):
    fn = config.get("WEATHER_ICONS_LOCATION")    
    return FileResponse(fn,headers={"Cache-Control":"no-cache"})


@app.get("/weather/default")
def get_weather():        
    return get_weather_data(config.get("DEF_DAYS_AHEAD"),config.get("LONG_LAT"),config.get("WEATHER_API_KEY"))
