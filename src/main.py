import customtkinter as ctk
from settings import *
from gui import menubar, annoucements


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.geometry(f'{str(WIDTH)}x{str(HEIGHT)}')
        self.title('Spotify Exceed')

        menubar.create_menu_bar(self, FONT_MENUBAR)
        annoucements.create_list_annoucements(self)
        # mainloop
        self.mainloop()


if __name__ == '__main__':
    App()
