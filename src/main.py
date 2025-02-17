import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import schedule
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from playsound import playsound
import threading
import time
import json
import os
from settings import *

ARQUIVO_JSON = "agendamentos.json"


def start_scheduler():
    """Inicia uma thread para rodar o agendador em segundo plano"""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.title('Exceed Anúncios')
        self.rowconfigure((0, 1, 2), weight=1)
        self.columnconfigure((0, 1, 2), weight=1)

        self.add_frame = Add(self)
        self.add_frame.grid(row=1, column=1, padx=20, pady=20)

        start_scheduler()

        self.mainloop()


class Add(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent)

        self.button_path = ctk.CTkButton(self, text='Selecionar Arquivo', command=self.add_mov)
        self.button_path.grid(row=0, column=0, pady=5, padx=5)

        self.entry_path = ctk.CTkEntry(self, width=250)
        self.entry_path.grid(row=0, column=1, pady=5, padx=5)

        self.entry_hour = ctk.CTkEntry(self, width=100)
        self.entry_hour.insert(0, 'HH:MM')
        self.entry_hour.grid(row=1, column=1, pady=5, padx=5)

        self.label_hour = ctk.CTkLabel(self, text='Horário')
        self.label_hour.grid(row=1, column=0, pady=5)

        self.entry_repeats = ctk.CTkEntry(self, width=100)
        self.entry_repeats.grid(row=2, column=1, pady=5, padx=5)

        self.label_repeats = ctk.CTkLabel(self, text='Repetições: ')
        self.label_repeats.grid(row=2, column=0, pady=5, padx=5)

        # Controle deslizante para ajustar o volume do anúncio
        self.label_volume = ctk.CTkLabel(self, text='Volume do Anúncio (%):')
        self.label_volume.grid(row=3, column=0, pady=5, padx=5)

        self.slider_volume = ctk.CTkSlider(self, from_=0, to=100)
        self.slider_volume.set(100)  # Volume padrão em 100%
        self.slider_volume.grid(row=3, column=1, pady=5, padx=5)

        self.schedule_button = ctk.CTkButton(self, text='Agendar Anúncio', command=self.schedule_music)
        self.schedule_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.listbox = tk.Listbox(self, width=50, height=10)
        self.listbox.grid(row=5, column=0, columnspan=2, pady=10)

        # Adiciona o evento de clique ao Listbox
        self.listbox.bind('<Button-1>', self.on_item_click)

        # Adiciona o evento de teclado para a tecla Delete
        self.listbox.bind('<Delete>', self.remove_selected_item)

        self.load_agendamentos()

    def add_mov(self):
        """Abre o explorador de arquivos para selecionar um MOV"""
        path = filedialog.askopenfilename()
        if path:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, path)

    def schedule_music(self):
        """Agenda a execução do arquivo no horário especificado e salva no JSON"""
        path = self.entry_path.get()
        hour = self.entry_hour.get()
        repeats = self.entry_repeats.get()
        volume = int(self.slider_volume.get())

        try:
            repeats = int(repeats)
        except ValueError:
            messagebox.showerror('Erro', 'Insira um número válido de repetições!')
            return

        if not path or not hour or repeats <= 0:
            messagebox.showerror('Erro', 'Selecione um arquivo, insira um horário válido e um número de repetições válido!')
            return

        try:
            schedule.every().day.at(hour).do(lambda: self.execute_and_remove(path, hour, repeats, volume))

            agendamentos = self.load_from_json()
            agendamentos.append({"horario": hour, "arquivo": path, "repeticoes": repeats, "volume": volume})
            self.save_to_json(agendamentos)

            self.listbox.insert(tk.END, f"{hour} - {os.path.basename(path)} ({repeats}x) - Volume: {volume}%")

            messagebox.showinfo('Sucesso', f'Música agendada para {hour} e será tocada {repeats} vezes com volume {volume}%.')
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao agendar: {e}')

    def execute_and_remove(self, path, hour, repeats, volume):
        """Executa o arquivo MOV e remove da lista da interface após tocar, repetindo X vezes"""
        for _ in range(repeats):
            self.play_music(path, volume)

        for i in range(self.listbox.size()):
            item_text = self.listbox.get(i)
            if item_text.startswith(hour):
                self.listbox.delete(i)
                break

    def alterar_volume_spotify(self, modo="diminuir"):
        """Diminui ou restaura o volume do Spotify no mixer de áudio."""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)

            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                volume_control = session.SimpleAudioVolume
                if session.Process and session.Process.name().lower() == "spotify.exe":
                    if modo == "diminuir":
                        volume_control.SetMasterVolume(0.2, None)  # 20% do volume original
                    elif modo == "restaurar":
                        volume_control.SetMasterVolume(1.0, None)  # Volume total
        except Exception as e:
            print(f"Erro ao alterar volume do Spotify: {e}")

    def play_music(self, path, volume):
        """Toca o anúncio com o volume especificado."""
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_interface = interface.QueryInterface(IAudioEndpointVolume)
        volume_original = volume_interface.GetMasterVolumeLevelScalar()

        volume_interface.SetMasterVolumeLevelScalar(volume / 100, None)

        playsound(path)

        volume_interface.SetMasterVolumeLevelScalar(volume_original, None)

    def load_agendamentos(self):
        """Carrega os agendamentos do JSON e agenda novamente"""
        agendamentos = self.load_from_json()
        for agendamento in agendamentos:
            schedule.every().day.at(agendamento["horario"]).do(
                lambda path=agendamento["arquivo"], hour=agendamento["horario"], repeats=agendamento["repeticoes"], volume=agendamento["volume"]:
                self.execute_and_remove(path, hour, repeats, volume)
            )

            self.listbox.insert(tk.END, f"{agendamento['horario']} - {os.path.basename(agendamento['arquivo'])} ({agendamento['repeticoes']}x) - Volume: {agendamento['volume']}%")

    def on_item_click(self, event):
        """Função chamada quando um item da lista é clicado"""
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            messagebox.showinfo("Item Selecionado", f"Você clicou em: {selected_item}")

    def remove_selected_item(self, event):
        """Remove o item selecionado da lista e do JSON"""
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            confirm = messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover:\n{selected_item}?")
            if confirm:
                self.listbox.delete(selected_index)

                # Remove do JSON
                agendamentos = self.load_from_json()
                horario = selected_item.split(" - ")[0]  # Extrai o horário do item selecionado
                agendamentos = [agendamento for agendamento in agendamentos if agendamento["horario"] != horario]
                self.save_to_json(agendamentos)

                messagebox.showinfo("Sucesso", "Anúncio removido com sucesso!")
        else:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")

    @staticmethod
    def load_from_json():
        """Lê os agendamentos do arquivo JSON"""
        if os.path.exists(ARQUIVO_JSON):
            with open(ARQUIVO_JSON, "r") as file:
                return json.load(file)
        return []

    @staticmethod
    def save_to_json(data):
        """Salva os agendamentos no arquivo JSON"""
        with open(ARQUIVO_JSON, "w") as file:
            json.dump(data, file, indent=4)


if __name__ == '__main__':
    App()