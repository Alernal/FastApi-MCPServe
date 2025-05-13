import os
import requests
from dotenv import load_dotenv
from rich.console import Console

console = Console()
load_dotenv()

def get_weather_country(country: str):
    access_key = os.environ.get("ACCESS_KEY")
    url = f"http://api.weatherstack.com/current?access_key={access_key}&query={country}"
    response = requests.get(url)
    data = response.json()
    return data.get("current", {})
