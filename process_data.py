import pandas as pd
import pytz

def preprocess_slot_entrie(all_time_entries):
    # Convierte la lista de entradas de tiempo en DataFrame
    slot_entrie_df = pd.DataFrame(all_time_entries)

    # Convertir las columnas al tipo de datos correspondiente
    slot_entrie_df['start'] = pd.to_datetime(slot_entrie_df['start'])
    slot_entrie_df['stop'] = pd.to_datetime(slot_entrie_df['stop'])
    slot_entrie_df['at'] = pd.to_datetime(slot_entrie_df['at'])
    slot_entrie_df['duration'] = slot_entrie_df['duration'] / 3600  # convierte los segundos en horas
    slot_entrie_df = slot_entrie_df.convert_dtypes()
    slot_entrie_df['pid'] = slot_entrie_df['pid'].astype(str)

    # Reemplaza los valores nulos en las columnas 'tags' y 'description'
    slot_entrie_df['tags'].fillna('Otras etiquetas', inplace=True)
    slot_entrie_df['description'].fillna('Otras descripciones', inplace=True)

    # Convertir las listas en cadenas en la columna 'tags'
    slot_entrie_df['tags'] = slot_entrie_df['tags'].astype(str)

    # Agregar prefijo "slot_entrie_" a las columnas
    slot_entrie_df = slot_entrie_df.add_prefix('slot_entrie_')

    return slot_entrie_df

def preprocess_projects(projects):
    # Convierte la lista de proyectos en DataFrame
    projects_df = pd.DataFrame(projects)

    # Convertir la columna "project_id" al tipo de datos string
    projects_df['id'] = projects_df['id'].astype(str)
    projects_df['name'].fillna('Otros Proyectos', inplace=True)

    # Agregar prefijo "project_" a las columnas
    projects_df = projects_df.add_prefix('project_')

    return projects_df

def filter_by_dates(slot_entrie_df, start_date, end_date):
    # Define el intervalo de fechas y conviértelo a UTC
    tz = pytz.timezone('UTC')
    start_date = pd.to_datetime(start_date).tz_localize(None).tz_localize(tz)
    end_date = pd.to_datetime(end_date).tz_localize(None).tz_localize(tz)

    # Filtra los datos por el intervalo temporal deseado
    mask = (slot_entrie_df['slot_entrie_start'] >= start_date) & (slot_entrie_df['slot_entrie_stop'] <= end_date)
    filtered_slot_entrie_df = slot_entrie_df.loc[mask]

    return filtered_slot_entrie_df

def process_data(projects, all_time_entries, start_date, end_date):
    slot_entrie_df = preprocess_slot_entrie(all_time_entries)
    projects_df = preprocess_projects(projects)
    filtered_slot_entrie_df = filter_by_dates(slot_entrie_df, start_date, end_date)

    # Merge con projects_df
    merged_df = filtered_slot_entrie_df.merge(projects_df, left_on='slot_entrie_pid', right_on='project_id', how='left')

    # Rellena los valores NaN en la columna 'project_name' con 'Otros proyectos'
    merged_df['project_name'] = merged_df['project_name'].fillna('Otros proyectos')

    return merged_df

# Define the process_descriptions_table_data function
def process_descriptions_table_data(projects, all_time_entries, start_date, end_date):
    merged_df = process_data(projects, all_time_entries, start_date, end_date)

    # Convertir las listas en cadenas para que se pueda realizar la factorización
    merged_df['slot_entrie_tags'] = merged_df['slot_entrie_tags'].astype(str)

    # Calcula el tiempo total para el intervalo de tiempo seleccionado
    total_time = merged_df['slot_entrie_duration'].sum()

    # Agrupa los datos por la descripción de la tarea y calcula el tiempo total para cada tarea
    descriptions_data = merged_df.groupby(['project_name', 'slot_entrie_description'])['slot_entrie_duration'].sum().reset_index()

    # Ordena los datos por la duración total en orden descendente
    descriptions_data = descriptions_data.sort_values(by='slot_entrie_duration', ascending=False)

    # Calcula el porcentaje de tiempo utilizado para cada tarea
    descriptions_data['percentage'] = (descriptions_data['slot_entrie_duration'] / total_time) * 100

    # Redondea la duración y el porcentaje a dos decimales
    descriptions_data['slot_entrie_duration'] = descriptions_data['slot_entrie_duration'].round(2)
    descriptions_data['percentage'] = descriptions_data['percentage'].round(2)

    return descriptions_data

def process_tags_table_data(projects, all_time_entries, start_date, end_date):
    merged_df = process_data(projects, all_time_entries, start_date, end_date)
    
    # Calculate the total time for the selected time range
    total_time = merged_df['slot_entrie_duration'].sum()

    # Group the data by tag and calculate the total time for each tag
    tags_data = merged_df.groupby(['slot_entrie_tags'])['slot_entrie_duration'].sum().reset_index()

    # Calculate the percentage of time used for each tag
    tags_data['percentage'] = (tags_data['slot_entrie_duration'] / total_time) * 100

    # Round the duration and percentage to two decimal places
    tags_data['slot_entrie_duration'] = tags_data['slot_entrie_duration'].round(2)
    tags_data['percentage'] = tags_data['percentage'].round(2)

    return tags_data


