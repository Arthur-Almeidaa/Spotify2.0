import tkinter as tk


def create_menu_bar(app, font):
    menu_bar = tk.Menu(app)
    help_menu = tk.Menu(menu_bar, tearoff=0)

    help_menu.add_separator()

    help_menu.add_command(label='Adicionar', font=font)
    help_menu.add_command(label='Remover', font=font)
    help_menu.add_command(label='Ajuda', font=font)
    
    help_menu.add_separator()

    menu_bar.add_cascade(label='Arquivo', menu=help_menu, font=font)
    app.config(menu=menu_bar)
