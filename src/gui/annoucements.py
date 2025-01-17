import customtkinter as ctk
from src import json_funcs
import os


FILE = os.path.abspath(os.path.join('src', 'gui', 'hours.json'))
file = json_funcs.load_data(FILE)

def create_list_annoucements(app):
    frame = ctk.CTkFrame(app, fg_color='white', width=250, height=250)
    frame.grid_propagate(True)
    frame.rowconfigure(len(file), weight=1)
    frame.grid(padx=50, pady=50)

    add_items_label(frame)

def add_items_label(frame):
    index = 0
    labels = []

    for anuncio, horario in file.items():
        index += 1
        label = ctk.CTkLabel(frame, text=f'{anuncio} {horario}')
        label.grid(row=index, padx=10, pady=5)
        labels.append(label)

def update_list(frame, labels):
    for label in labels:
        label.grid_forget()
    add_items_label(frame)
