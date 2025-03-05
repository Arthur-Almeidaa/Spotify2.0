import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import schedule
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import pythoncom
from playsound import playsound
import threading
import time
import json
import os

ARQUIVO_JSON = "agendamentos.json"
SETTINGS_JSON = "settings.json"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_from_json(SETTINGS_JSON)
        self.geometry(f'{self.settings['width']}x{self.settings['height']}')
        self.title('Exceed Anúncios')
        self.rowconfigure((0, 1, 2), weight=1)
        self.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.configure(fg_color=f'{self.settings['background_color']}')

        # Inicializa o COM
        pythoncom.CoInitialize()

        self.add_frame = Add(self)
        self.add_frame.grid(row=1, column=2, padx=20, pady=20)

        self.start_scheduler()

        self.mainloop()

    def start_scheduler(self):
        """Inicia uma thread para rodar o agendador em segundo plano"""

        def run_scheduler():
            # Inicializa o COM na thread
            pythoncom.CoInitialize()
            while True:
                schedule.run_pending()
                time.sleep(1)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()


class Add(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent)
        self.settings = load_from_json(SETTINGS_JSON)
        self.configure(fg_color=f'{self.settings['frame_color']}')
        self.button_path = ctk.CTkButton(self, text='Selecionar Arquivo', command=self.add_mov)
        self.button_path.grid(row=0, sticky='ew', column=0, padx=20, columnspan=2, pady=5)

        self.path = ctk.CTkEntry(self)

        self.entry_hour = ctk.CTkEntry(self, width=100)
        self.entry_hour.insert(0, 'HH:MM')
        self.entry_hour.grid(row=1, column=1, pady=5, padx=5)

        self.entry_repeats = ctk.CTkEntry(self, width=100)
        self.entry_repeats.insert(0, '1')
        self.entry_repeats.grid(row=2, column=1, pady=5, padx=5)

        self.entry_repeats.bind('<Return>', self.schedule_music)
        self.entry_hour.bind('<Return>', self.schedule_music)

        self.label_repeats = ctk.CTkLabel(self, text='Repetições: ')
        self.label_repeats.grid(row=2, column=0, pady=5, padx=5)

        self.schedule_label = ctk.CTkLabel(self, text='Agendar Anúncio')
        self.schedule_label.grid(row=1, column=0, pady=10)

        self.listbox = tk.Listbox(self, width=50, height=10)
        self.listbox.grid(row=3, column=0, columnspan=2, pady=10, padx=20)

        # Adiciona o evento de clique ao Listbox
        self.listbox.bind('<Button-1>', self.on_item_click)

        # Adiciona o evento de teclado para a tecla Delete
        self.listbox.bind('<Delete>', self.remove_selected_item)

        self.load_agendamentos()

        # Agenda a função para diminuir o volume do Spotify às 11:00
        schedule.every().day.at(f'{self.settings['final_hour']}').do(self.alterar_volume_spotify, modo="diminuir")

        # Agenda a função para restaurar o volume do Spotify às 9:00
        schedule.every().day.at(f'{self.settings['start_hour']}').do(self.alterar_volume_spotify, modo="restaurar")

    def add_mov(self):
        """Abre o explorador de arquivos para selecionar um MP4"""
        path = filedialog.askopenfilename()
        self.path.insert(0, path)


    def schedule_music(self, event):
        """Agenda a execução do arquivo no horário especificado e salva no JSON"""
        path = self.path.get()
        self.path.delete(0, 'end')
        hour = self.entry_hour.get()
        repeats = self.entry_repeats.get()

        try:
            repeats = int(repeats)
        except ValueError:
            messagebox.showerror('Erro', 'Insira um número válido de repetições!')
            return

        if not path or not hour or repeats <= 0:
            messagebox.showerror('Erro',
                                 'Selecione um arquivo, insira um horário válido e um número de repetições válido!')
            return

        try:
            schedule.every().day.at(hour).do(lambda: self.execute_and_remove(path, hour, repeats))

            agendamentos = load_from_json(ARQUIVO_JSON)
            agendamentos.append({"horario": hour, "arquivo": path, "repeticoes": repeats})
            save_to_json(agendamentos)

            # Atualiza a Listbox com os agendamentos ordenados
            self.update_listbox()

            messagebox.showinfo('Sucesso', f'Música agendada para {hour} e será tocada {repeats} vezes.')
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao agendar: {e}')

    def execute_and_remove(self, path, hour, repeats):
        """Executa o arquivo MP4 e remove da lista da interface após tocar, repetindo X vezes"""
        for _ in range(repeats):
            self.play_music(path)

        for i in range(self.listbox.size()):
            item_text = self.listbox.get(i)
            if item_text.startswith(hour):
                self.listbox.delete(i)
                break

    def alterar_volume_spotify(self, modo):
        """Diminui ou restaura o volume do Spotify no mixer de áudio."""
        try:

            # Inicializa o COM na thread
            pythoncom.CoInitialize()

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

            volume = interface.QueryInterface(IAudioEndpointVolume)

            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                volume_control = session.SimpleAudioVolume

                if session.Process and session.Process.name().lower() == "spotify.exe":
                    if modo == "diminuir":
                        volume_control.SetMasterVolume(0.0 if datetime.datetime.now().hour == f'{self.settings['final_hour'.split(':')[0]]}' else 0.2, None)

                    elif modo == "restaurar":
                        volume_control.SetMasterVolume(1.0, None)

        except Exception as e:
            print(f"Erro ao alterar volume do Spotify: {e}")
        finally:
            # Libera o COM após o uso
            pythoncom.CoUninitialize()

    def play_music(self, path):
        """Reduz o volume do Spotify, toca o anúncio e depois restaura o volume."""
        self.alterar_volume_spotify("diminuir")
        playsound(path)
        self.alterar_volume_spotify("restaurar")

    def load_agendamentos(self):
        """Carrega os agendamentos do JSON e agenda novamente"""
        agendamentos = load_from_json(ARQUIVO_JSON)
        for agendamento in agendamentos:
            schedule.every().day.at(agendamento["horario"]).do(
                lambda: self.execute_and_remove(agendamento["arquivo"], agendamento["horario"],
                                                agendamento["repeticoes"]))

        # Atualiza a Listbox com os agendamentos ordenados
        self.update_listbox()

    def update_listbox(self):
        """Atualiza a Listbox com os agendamentos ordenados por horário"""
        self.listbox.delete(0, tk.END)  # Limpa a Listbox

        # Carrega os agendamentos e ordena por horário
        agendamentos = load_from_json(ARQUIVO_JSON)
        agendamentos_ordenados = sorted(agendamentos, key=lambda x: x["horario"])

        # Insere os agendamentos ordenados na Listbox
        for agendamento in agendamentos_ordenados:
            self.listbox.insert(tk.END,
                                f"{agendamento['horario']} - {os.path.basename(agendamento['arquivo'])} ({agendamento['repeticoes']}x)")

    def on_item_click(self, event):
        """Função chamada quando um item da lista é clicado"""
        selected_index = self.listbox.curselection()

    def remove_selected_item(self, event):
        """Remove o item selecionado da lista e do JSON"""
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            confirm = messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover:\n{selected_item}?")
            if confirm:
                # Remove da lista de exibição
                self.listbox.delete(selected_index)

                # Remove do JSON
                agendamentos = load_from_json(ARQUIVO_JSON)
                horario = selected_item.split(" - ")[0]  # Extrai o horário do item selecionado
                agendamentos = [agendamento for agendamento in agendamentos if agendamento["horario"] != horario]
                save_to_json(agendamentos)

                # Atualiza a Listbox
                self.update_listbox()
        else:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")


def load_from_json(f):
    """Lê os agendamentos do arquivo JSON"""
    if os.path.exists(f):
        with open(f, "r") as file:
            return json.load(file)
    return []


def save_to_json(data):
    """Salva os agendamentos no arquivo JSON"""
    with open(ARQUIVO_JSON, "w") as file:
        json.dump(data, file, indent=4)


if __name__ == '__main__':
    App()