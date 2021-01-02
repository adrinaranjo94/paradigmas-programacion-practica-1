from tkinter import *
from tkinter.ttk import Progressbar
from rx import *
from tkinter.ttk import Combobox
from bs4 import BeautifulSoup
import requests
import threading
import asyncio

bg_color = '#3E4149'

class App:
    def __init__(self,_async_loop):
        self.async_loop = _async_loop
        self.imgs = {}
        self.imgs_length = 0
        # Build TK
        self.window = Tk()
        self.window.title = 'Aplicación Gráfica!'
        self.window.geometry('650x450')
        self.window.resizable(False, False)
        self.window.configure(bg=bg_color)

        # Build search
        self.search = Entry()

        self.search.grid(column=0, row=1, columnspan=4)

        self.button_search = Button(text='Buscar', width=35, command=self.search_button, highlightbackground=bg_color).grid(column=0, row=2,columnspan=2, )
        self.listbox = Listbox()
        self.listbox.grid(column=0, row=3)

        self.status_download_files = Label(text="", bg=bg_color)
        self.status_download_files.grid(column=0, row=4)

        self.progress_bar = Progressbar(self.window, orient=HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.grid_forget()

        self.window.mainloop()

    def initialize_flow_download(self):
        self.imgs = {}
        self.imgs_length = 0
        self.listbox.delete(0, END)
        self.progress_bar.grid(column=0, row=5, columnspan=4)

    def _asyncio_thread(self, _imgs, observer):
        self.async_loop.run_until_complete(self.download_images(_imgs, observer))

    async def download_images(self, _imgs, observer):
        downloads = [self.download_image(img) for img in _imgs]
        await asyncio.wait(downloads)
        observer.on_completed()

    def observable_search_button(self, url):
        def search_page(o, s):
            content = requests.get(url)
            soup = BeautifulSoup(content.text, 'html.parser')
            _imgs = soup.find_all('img')
            self.imgs_length = len(_imgs)
            self.status_download_files.config(text=f'Se han descargado 0 de {self.imgs_length} imagenes')
            threading.Thread(target=self._asyncio_thread, args=(_imgs, o,)).start()
        return create(search_page)

    async def download_image(self, img):
        img_downloaded = requests.get(img["src"])
        self.imgs[f'{img["alt"]}_{self.listbox.size()}'] = img_downloaded
        self.listbox.insert(self.listbox.size()+1, img["alt"] or f'Imagen {self.listbox.size()+1}')
        self.status_download_files.config(text=f'Se han descargado {self.listbox.size()} de {self.imgs_length} imagenes',
                                          bg=bg_color)
        self.progress_bar.config(value=self.listbox.size()*100/self.imgs_length)
        #self.window.update()

    def download_completed(self):
        self.status_download_files.configure(text=f'Descarga finalizada de las {self.imgs_length} imagenes')
        self.progress_bar.grid_forget()

    def search_button(self):
        self.initialize_flow_download()
        self.observable_search_button(self.search.get()).subscribe(on_completed=self.download_completed)


if __name__ == '__main__':
    async_loop = asyncio.get_event_loop()
    App(async_loop)
