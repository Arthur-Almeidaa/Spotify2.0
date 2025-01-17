import customtkinter as ctk

def create_current(app, current_music_playing):
    ctk.CTkLabel(app, text=f'{current_music_playing}').place()
