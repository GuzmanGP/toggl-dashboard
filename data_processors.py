import pandas as pd
import pytz
import json
import logging
from ORM import save_data_to_db
import re
from datetime import datetime, timedelta

'''
slot_entries: 
id	guid	wid	billable	start	stop	duration	tags	duronly	at	uid	pid	description
0	3065685248	05f8108602cd06a3541a4789110fc03f	7464902	True	2023-07-28T08:49:53+00:00	2023-07-28T08:49:53+00:00	0	[Formación / Investigación / Brain Storming]	True	2023-07-28T08:50:24+00:00	9577449	NaN	NaN
1	3065685599	7f425c8c8fd4bf04bbcf47a8940480a6	7464902	True	2023-07-28T08:50:41+00:00	2023-07-28T09:01:53+00:00	672	[Formación / Investigación / Brain Storming]	True	2023-07-28T09:01:53+00:00	9577449	193974151.0	tirea
'''

import pandas as pd
import re

def extract_tag_patterns(s):
    if isinstance(s, list):  # Asegúrate de que s es una lista
        patterns = [re.match(r'\[(\w{2})\]', string).group(1) for string in s if re.match(r'\[(\w{2})\]', string)]  # Busca todas las coincidencias
        return patterns if patterns else None  # Retorna las coincidencias o None si no se encuentra ninguna
    else:
        return None  # Retorna None si s no es una lista

def get_unique_patterns(df, tag_column):
    df['tag_patterns'] = df[tag_column].apply(extract_tag_patterns)
    tag_patterns = list(set([item for sublist in df['tag_patterns'].dropna().tolist() for item in sublist]))
    df.drop('tag_patterns', axis=1, inplace=True)
    return tag_patterns

def filter_tags(s, tag_pattern):
    if isinstance(s, list):  # Asegúrate de que s es una lista
        pattern = r'\[{}\]\s*(.+)'.format(tag_pattern)  # Define el patrón para buscar las cadenas que siguen a "[XX] "
        values = [re.search(pattern, string).group(1) for string in s if re.search(pattern, string)]  # Busca todas las coincidencias
        return values[0] if values else ""  # Retorna las coincidencias o None si no se encuentra ninguna
    else:
        return None  # Retorna None si s no es una lista

def apply_tag_extraction(df, tag_column):
    tag_patterns = get_unique_patterns(df, tag_column)
    for tag_pattern in tag_patterns:
        df[f'tags_{tag_pattern}'] = df[tag_column].apply(lambda x: filter_tags(x, tag_pattern))
    return df




def preprocess_slot_entrie(all_time_entries):
    # Convierte la lista de entradas de tiempo en DataFrame
    slot_entrie_df = pd.DataFrame(all_time_entries)

    slot_entrie_df = apply_tag_extraction(slot_entrie_df , 'tags')

    # Asegúrate de que la columna 'start' es de tipo datetime
    slot_entrie_df['start'] = pd.to_datetime(slot_entrie_df['start'])
    slot_entrie_df['stop'] = pd.to_datetime(slot_entrie_df['stop'])
    slot_entrie_df['at'] = pd.to_datetime(slot_entrie_df['at'])
    slot_entrie_df['duration'] = slot_entrie_df['duration'] / 60  # convierte los segundos en minutos

    # Extrae solo la fecha (día) de la columna 'start'
    slot_entrie_df['start_day'] = slot_entrie_df['start'].dt.date
    # Agrupa por 'start_day' y crea una nueva columna 'counter' que enumera las entradas dentro de cada grupo
    slot_entrie_df['counter'] = slot_entrie_df.groupby('start_day').cumcount() + 1


    # Ordenar los valores por 'start_day' y 'start'
    slot_entrie_df = slot_entrie_df.sort_values(['start_day', 'start'])
    # Calcular la diferencia de tiempo en minutos entre el 'stop' de la entrada anterior y la 'start' de la entrada actual
    slot_entrie_df['time_diff'] = slot_entrie_df.groupby('start_day')['start'].diff().dt.total_seconds().fillna(0) / 60
    # Si la 'time_diff' es negativa (lo que puede suceder si las entradas no están perfectamente ordenadas), establecerla en 0
    slot_entrie_df['time_diff'] = slot_entrie_df['time_diff'].apply(lambda x: max(x, 0))
    # Eliminar la columna 'start_day'
    slot_entrie_df = slot_entrie_df.drop(columns='start_day')


    # Calcula el tiempo excedido
    stop_diff = slot_entrie_df['stop'].diff().dt.total_seconds() / 60  # convierte la diferencia a minutos
    slot_entrie_df['excess_time'] = -1 * (slot_entrie_df['duration'] - stop_diff)

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
    projects_df = projects_df[['id','name']].add_prefix('project_')

    return projects_df


def filter_by_dates(slot_entrie_df, start_date=None, end_date=None):
    # Define el intervalo de fechas y conviértelo a UTC
    tz = pytz.timezone('UTC')
    
    if not start_date:
        # Si la fecha de inicio no se proporciona, establece la fecha de inicio como la fecha de hoy
        start_date = datetime.now().date() - timedelta(days=5*365)
    
    if not end_date:
        # Si la fecha de fin no se proporciona, establece la fecha de fin como la fecha de hoy más 5 años
        end_date = start_date + timedelta(days=5*365)
    
    start_date = pd.to_datetime(start_date).tz_localize(None).tz_localize(tz)
    end_date = pd.to_datetime(end_date).tz_localize(None).tz_localize(tz)

    # Filtra los datos por el intervalo temporal deseado
    mask = (slot_entrie_df['slot_entrie_start'] >= start_date) & (slot_entrie_df['slot_entrie_stop'] <= end_date)
    filtered_slot_entrie_df = slot_entrie_df.loc[mask]

    return filtered_slot_entrie_df


def process_data(projects, all_time_entries, start_date=None, end_date=None):
    slot_entrie_df = preprocess_slot_entrie(all_time_entries)
    projects_df = preprocess_projects(projects)
    
    filtered_slot_entrie_df = filter_by_dates(slot_entrie_df, start_date, end_date)

    # Merge con projects_df
    merged_df = filtered_slot_entrie_df.merge(projects_df, left_on='slot_entrie_pid', right_on='project_id', how='left')

    # Rellena los valores NaN en la columna 'project_name' con 'Otros proyectos'
    merged_df['project_name'] = merged_df['project_name'].fillna('Otros proyectos')
    
    merged_df = merged_df.drop(['slot_entrie_duronly', 'slot_entrie_tags', 'slot_entrie_id', 'slot_entrie_guid', 'slot_entrie_wid', 'slot_entrie_billable', 'slot_entrie_uid',	'slot_entrie_pid', 'project_id'], axis=1)
    cols_to_move = ["slot_entrie_at", "slot_entrie_counter", "project_name", "slot_entrie_tags_TA", "slot_entrie_start",
                    "slot_entrie_stop", "slot_entrie_duration", "slot_entrie_time_diff",
                    "slot_entrie_excess_time", "slot_entrie_description"]

    # Get a list of the remaining columns and extend it with cols_to_move
    new_order = cols_to_move + [col for col in merged_df.columns if col not in cols_to_move] 

    # Reorder the columns
    merged_df = merged_df[new_order]

    save_data_to_db(merged_df, 'slot_entries')

    return merged_df

'''
slot_entrie_id	slot_entrie_guid	slot_entrie_wid	slot_entrie_billable	slot_entrie_start	slot_entrie_stop	slot_entrie_duration	slot_entrie_tags	slot_entrie_duronly	slot_entrie_at	slot_entrie_uid	slot_entrie_pid	slot_entrie_description	slot_entrie_tags_TA	slot_entrie_tags_DI	slot_entrie_counter	slot_entrie_time_diff	slot_entrie_excess_time	project_id	project_name
0	3065685248	05f8108602cd06a3541a4789110fc03f	7464902	True	2023-07-28 08:49:53+00:00	2023-07-28 08:49:53+00:00	0.0	['[TA] Formación / Investigación / Brain Storm...	True	2023-07-28 08:50:24+00:00	9577449	<NA>	Otras descripciones	Formación / Investigación / Brain Storming		1	0.0	<NA>	NaN	Otros proyectos
1	3065685599	7f425c8c8fd4bf04bbcf47a8940480a6	7464902	True	2023-07-28 08:50:41+00:00	2023-07-28 09:01:53+00:00	11.2	['[TA] Formación / Investigación / Brain Storm...	True	2023-07-28 09:01:53+00:00	9577449	193974151	tirea	Formación / Investigación / Brain Storming		2	0.8	-0.8	193974151	TIREA

'''
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

    save_data_to_db(tags_data, 'tags_data')


def filter_ta_tags(tags_str, tag_pattern):
    try:
        # Intentamos convertir el string a una lista
        tags_list = json.loads(tags_str)

        # Filtramos la lista para seleccionar solo las tags que contienen "TA -"
        ta_tags = list(filter(lambda tag: tag_pattern in tag, tags_list))
    except Exception as e:
        logging.debug(e)
        return None
    
    return ta_tags if ta_tags else None




if __name__ == "__main__":


    pass