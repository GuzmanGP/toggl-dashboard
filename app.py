from data_processors import *
import toggl_api
from datetime import datetime as dt
import pandas as pd

pd.set_option('display.max_columns', None)

if __name__ == "__main__":
    # Get the projects and time entries data from the Toggl API
    projects = toggl_api.get_projects()
    all_time_entries = toggl_api.get_all_time_entries()

    process_data(projects, all_time_entries, start_date=None, end_date=None)
