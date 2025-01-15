import json
from tkinter import messagebox
import os
import uuid


def load_data(file):
    """ Helper function to load JSON data from a file"""

    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(file, data):
    """ Helper function to save JSON data to a file"""

    with open(file, 'w') as f:
        json.dump(data, f, indent=1)


def delete_value(file, value):
    """
    Deletes a specific key-value pair from the JSON file based on the provided value

    Parameters:
    file (str): path to the JSON file
    value (str): the key to delete from the JSON file
    """

    dados = load_data(file)

    if value in dados.keys():
        updated_data = {key: value for key, value in dados.items() if key != value}
        save_data(file, updated_data)
    else:
        messagebox.showerror(title='Erro', message='Anúncio não encontrado')


def add_value(file, path, hour):
    """
    Adds a new entry to the JSON file with a unique key and the provided path and hour

    Parameters:
    file (str): path to the json file
    path (str): file path for the announcement
    hour (str): hour for the announcement
    """

    dados = load_data(file)

    key = f'video{os.path.basename(path)}'

    if key in dados:
        key = key + f' {str(uuid.uuid1())[:4]}'
        dados[key] = [path, hour]
        save_data(file, dados)
    else:
        dados[key] = [path, hour]
        save_data(file, dados)
