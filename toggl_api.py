# toggl_api.py

import requests
import pandas as pd
from config import API_TOKEN, WORKSPACE_ID

auth = (API_TOKEN, 'api_token')

def get_projects():
    # Descarga la lista de todos los proyectos
    response = requests.get(f'https://api.track.toggl.com/api/v8/workspaces/{WORKSPACE_ID}/projects', auth=auth)
    projects = response.json()
    return projects

def get_all_time_entries():
    # Descarga todas las entradas de tiempo
    response = requests.get('https://api.track.toggl.com/api/v8/time_entries', auth=auth)
    all_time_entries = response.json()
    return all_time_entries

