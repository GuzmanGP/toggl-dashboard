from pymongo import MongoClient

# Los detalles de la base de datos
username = "pomodoro_slots"
password = "ck8IK2r81CNx8Ts2"
hostname = "cluster0.8fqmlw6.mongodb.net"
database_name = "pomodoro_db_slots"

# Crea la cadena de conexión
connection_string = f"mongodb+srv://{username}:{password}@{hostname}/{database_name}?retryWrites=true&w=majority"

# Crea el cliente de pymongo
client = MongoClient(connection_string)

def save_data_to_db(df, collection_name):
    """
    Guarda un DataFrame de pandas en la base de datos como una nueva colección

    Parameters:
    df (pandas.DataFrame): el DataFrame para guardar
    collection_name (str): el nombre de la colección en la base de datos
    """
    db = client[database_name]
    collection = db[collection_name]
    collection.insert_many(df.to_dict('records'))
