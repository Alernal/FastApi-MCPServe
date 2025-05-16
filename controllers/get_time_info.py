import requests
from rich.console import Console

console = Console()

def get_time_info(user_id: None):
    url = f"https://timeapi.io/api/Time/current/zone?timeZone=America/Bogota"
    response = requests.get(url)

    if response.status_code != 200:
        console.print(f"[red]Error al obtener los datos de tiempo: {response.status_code}[/red]")
        return {}

    data = response.json()

    # Extraemos información útil
    date_time = data.get("dateTime")
    time_zone = data.get("timeZone")
    day_of_week = data.get("dayOfWeek")
    utc_offset = data.get("utcOffset")

    return {
        "date_time": date_time,
        "time_zone": time_zone,
        "day_of_week": day_of_week,
        "utc_offset": utc_offset
    }