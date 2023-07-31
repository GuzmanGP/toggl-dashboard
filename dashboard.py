import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from datetime import datetime as dt, timedelta
import logging
from dateutil.relativedelta import relativedelta
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dash_table.Format import Group

# Import your data processing script
import process_data

# Import the Toggl API functions
import toggl_api

# Get the projects and time entries data from the Toggl API
projects = toggl_api.get_projects()
all_time_entries = toggl_api.get_all_time_entries()

# Define the default end date as yesterday
default_end_date = dt.now() 
# Define the default start date as one week before the end date
default_start_date = default_end_date - timedelta(7)

# Initialize the Dash app
app = dash.Dash(__name__)
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Toggl Data Dashboard"), width=12)
    ], justify='center', align='center'),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='time-range',
            options=[
                {'label': 'Semana actual', 'value': 'week'},
                {'label': 'Mes actual', 'value': 'month'},
                {'label': 'Trimestre actual', 'value': 'quarter'},
                {'label': 'Semestre actual', 'value': 'semester'},
                {'label': 'Año actual', 'value': 'year'}
            ],
            value='week',
            style={'font-size': '18px', 'width': '50%'}
        ), width=6),

        dbc.Col(dcc.DatePickerRange(
            id='my-date-picker-range',
            min_date_allowed=dt(2023, 1, 1),
            max_date_allowed=dt(2030, 12, 31),
            start_date=dt(2023, 1, 1),
            end_date=dt(2023, 12, 31),
            className='datepicker',
            style={'font-size': '18px', 'width': '50%'}
        ), width=6),
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='pie-chart-projects')
        ], width=6),
        dbc.Col([
            dcc.Graph(id='treemap-chart')
        ], width=6),
    ]),

    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                id='tags-table',
                columns=[
                    {'name': 'Tarea', 'id': 'slot_entrie_tags'},
                    {'name': 'Tiempo acumulado', 'id': 'slot_entrie_duration'},
                    {'name': '% del tiempo acumulado', 'id': 'percentage'}
                ],
                sort_action='native',
                sort_mode='multi'
            ),
        ], width=6),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='treemap-chart-description'), width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                id='descriptions-table',
                columns=[
                    {'name': 'Proyecto', 'id': 'project_name'},
                    {'name': 'Tarea', 'id': 'slot_entrie_description'},
                    {'name': 'Tiempo acumulado', 'id': 'slot_entrie_duration'},
                    {'name': '% del tiempo acumulado', 'id': 'percentage'}
                ],
                sort_action='native',
                sort_mode='multi'
            ),
        ], width=6)
    ]),
    dbc.Row([dbc.Col(dcc.Graph(id='project-duration-cumulative-chart'), width=12)],),
    dbc.Row([dbc.Col(dcc.Graph(id='tags-duration-cumulative-chart'), width=12)],)

], fluid=True)

@app.callback(
    Output('my-date-picker-range', 'start_date'),
    Output('my-date-picker-range', 'end_date'),
    Input('time-range', 'value'))
def update_dates(time_range):
    today = dt.now()
    if time_range == 'week':
        start_date = today - timedelta(days=7)
    elif time_range == 'month':
        start_date = today - relativedelta(months=1)
    elif time_range == 'quarter':
        start_date = today - relativedelta(months=3)
    elif time_range == 'semester':
        start_date = today - relativedelta(months=6)
    elif time_range == 'year':
        start_date = today - relativedelta(years=1)
    else:
        start_date = default_start_date
    end_date = default_end_date
    return start_date, end_date


@app.callback(
    Output('treemap-chart', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_output(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    df = process_data.process_data(projects, all_time_entries, start_date, end_date)

    # Generate and return the treemap figure
    fig = px.treemap(df, path=['project_name', 'slot_entrie_tags'], title='Tipos de tareas')

    fig.update_traces(
        textinfo='label+percent root',
        insidetextfont={'color': 'white', 'size': 12},
        hoverinfo='label+percent root+value',
        hoverlabel=dict(
            bgcolor="white", 
            font_size=16, 
            font_family="Rockwell"
        )
    )
    
    return fig

@app.callback(
    Output('treemap-chart-description', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_output_description(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    df = process_data.process_data(projects, all_time_entries, start_date, end_date)

    # Generate and return the treemap figure
    fig = px.treemap(df, path=['project_name', 'slot_entrie_description'], title='Descripciones de las tareas')

    fig.update_traces(
        textinfo='label+percent root',
        insidetextfont={'color': 'white', 'size': 12},
        hoverinfo='label+percent root+value',
        hoverlabel=dict(
            bgcolor="white", 
            font_size=16, 
            font_family="Rockwell"
        )
    )
    
    return fig

@app.callback(
    Output('pie-chart-projects', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_pie_chart(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    df = process_data.process_data(projects, all_time_entries, start_date, end_date)

    # Generate and return the pie chart figure
    fig = px.pie(df, values='slot_entrie_duration', names='project_name', title='Proyectos')
    return fig

@app.callback(
    Output('descriptions-table', 'data'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_task_table(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    task_data = process_data.process_descriptions_table_data(projects, all_time_entries, start_date, end_date)

    return task_data.to_dict('records')

@app.callback(
    Output('tags-table', 'data'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_task_table(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    tags_data = process_data.process_tags_table_data(projects, all_time_entries, start_date, end_date)
   
    return tags_data.to_dict('records')


@app.callback(
    Output('project-duration-cumulative-chart', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_duration_cumulative_chart(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    df = process_data.process_data(projects, all_time_entries, start_date, end_date)

    # Convert 'slot_entrie_start' and 'slot_entrie_duration' to datetime and timedelta respectively
    df['slot_entrie_start'] = pd.to_datetime(df['slot_entrie_start'])
    df['slot_entrie_duration'] = pd.to_timedelta(df['slot_entrie_duration'], unit='s')

    # Create a new column for the end time of each task
    df['slot_entrie_end'] = df['slot_entrie_start'] + df['slot_entrie_duration']

    # Resample to get the total duration for each day
    df['date'] = df['slot_entrie_start'].dt.date
    df_grouped = df.groupby(['date', 'project_name'])['slot_entrie_duration'].sum().reset_index()

    # Convert the duration from timedelta to seconds
    df_grouped['slot_entrie_duration'] = df_grouped['slot_entrie_duration'].dt.total_seconds() / 3600
    print(df_grouped)
    # Calculate the average duration per day
    avg_daily_duration = df_grouped.groupby('date')['slot_entrie_duration'].sum().mean()

    # Generate the bar chart figure
    fig = px.bar(df_grouped, x='date', y='slot_entrie_duration', color='project_name',
                 title='Duración Acumulada de Proyectos por Día')

    # Move the legend to the bottom
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.5,
        xanchor="center",
        x=0.5
    ))

    # Get first and last active day
    first_active_day = df['date'].min()
    last_active_day = df['date'].max()

    # Add horizontal lines
    fig.add_shape(type="line",
                  x0=first_active_day, x1=last_active_day, y0=avg_daily_duration, y1=avg_daily_duration,
                  line=dict(color="Black", width=2, dash="dash"))
    '''
    fig.add_shape(type="line",
                  x0=first_active_day, x1=last_active_day, y0=6, y1=6,
                  line=dict(color="Black", width=2))
    '''
    return fig



@app.callback(
    Output('tags-duration-cumulative-chart', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date')])
def update_duration_cumulative_chart(start_date, end_date):
    # Convert input dates to datetime
    start_date = pd.to_datetime(start_date).tz_localize('UTC')
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Process the data and get the DataFrame
    df = process_data.process_data(projects, all_time_entries, start_date, end_date)
    
    # Convert 'slot_entrie_start' and 'slot_entrie_duration' to datetime and timedelta respectively
    df['slot_entrie_start'] = pd.to_datetime(df['slot_entrie_start'])
    df['slot_entrie_duration'] = pd.to_timedelta(df['slot_entrie_duration'], unit='s')

    # Create a new column for the end time of each task
    df['slot_entrie_end'] = df['slot_entrie_start'] + df['slot_entrie_duration']

    # Resample to get the total duration for each day
    df['date'] = df['slot_entrie_start'].dt.date
    df_grouped = df.groupby(['date', 'slot_entrie_tags'])['slot_entrie_duration'].sum().reset_index()

    # Convert the duration from timedelta to seconds
    df_grouped['slot_entrie_duration'] = df_grouped['slot_entrie_duration'].dt.total_seconds() / 3600
    print(df_grouped)
    # Calculate the average duration per day
    avg_daily_duration = df_grouped.groupby('date')['slot_entrie_duration'].sum().mean()

    # Generate the bar chart figure
    fig = px.bar(df_grouped, x='date', y='slot_entrie_duration', color='slot_entrie_tags',
                 title='Duración Acumulada de Tipo de Tareas por Día')

    # Move the legend to the bottom
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.5,
        xanchor="center",
        x=0.5
    ))

    # Get first and last active day
    first_active_day = df['date'].min()
    last_active_day = df['date'].max()

    # Add horizontal lines
    fig.add_shape(type="line",
                  x0=first_active_day, x1=last_active_day, y0=avg_daily_duration, y1=avg_daily_duration,
                  line=dict(color="Black", width=2, dash="dash"))
    '''
    fig.add_shape(type="line",
                  x0=first_active_day, x1=last_active_day, y0=6, y1=6,
                  line=dict(color="Black", width=2))
    '''
    return fig





if __name__ == '__main__':
    app.run_server(debug=True)
