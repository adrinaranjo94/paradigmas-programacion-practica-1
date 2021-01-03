from tkinter import *
from tkinter.ttk import Progressbar
from rx import *
from PIL import ImageTk, Image
from bs4 import BeautifulSoup
import requests
import threading
import asyncio
import io

bg_color = '#3E4149'


def resize_image(image, type):
    if type == "bytes":
        return Image.open(io.BytesIO(image)).resize((265, 265), Image.ANTIALIAS)
    elif type == "file":
        return Image.open(image).resize((265, 265), Image.ANTIALIAS)


class App:
    def __init__(self, _async_loop):
        self.async_loop = _async_loop
        self.imgs = {}
        self.imgs_length = 0
        self.img_selected = None
        # Build TK
        self.window = Tk()
        self.window.title = 'Aplicación Gráfica!'
        self.window.geometry('650x100')
        self.window.resizable(False, False)
        self.window.configure(bg=bg_color)

        # Build Title
        self.title_app = Label(text="URL a procesar", bg=bg_color, width=20)
        self.title_app.grid(column=0, row=1, padx=10)

        # Build search
        self.search = Entry(width=40)
        self.search.grid(column=1, row=1, pady=10, padx=5)

        # Build button search
        self.button_search = Button(text='Buscar', command=self.observe_search_button, highlightbackground=bg_color,
                                    width=10) \
            .grid(column=2, row=1)

        # Build listbox
        self.listbox = Listbox()
        self.listbox.grid_forget()
        self.listbox.bind("<<ListboxSelect>>", self.observe_select_item)

        # Build canvas
        self.canvas = Canvas(self.window, width=300, height=300)
        self.canvas.grid_forget()

        # Build label status download images
        self.status_download_files = Label(text="", bg=bg_color)
        self.status_download_files.grid_forget()

        # Build progress bar to show progress while downloading images
        self.progress_bar = Progressbar(self.window, orient=HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.grid_forget()

        self.window.mainloop()

    '''
        Method to initialize flow when user click on button search
    '''
    def initialize_flow_download(self):
        self.imgs = {}
        self.imgs_length = 0
        self.listbox.delete(0, END)
        self.listbox.grid(column=0, row=3, padx=10)
        self.status_download_files.grid(column=0, row=4, columnspan=3, sticky="se", pady=5)
        self.progress_bar.grid(column=1, row=5, columnspan=2, sticky="e")
        self.canvas.grid(row=3, column=1, columnspan=2)
        self.img_selected = None
        self.window.geometry('650x450')

    # START SECTION OBSERVABLE DOWNLOAD URL IMAGES
    '''
       Method to initialize async loop until complete download images
    '''
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
        try:
            img_downloaded = requests.get(img["src"])
            alt_img = f'{img["alt"] or "Imagen"}'
            alt_img_key = f'{alt_img}_{self.listbox.size()}'
            self.imgs[alt_img_key] = img_downloaded.content
            self.listbox.insert(self.listbox.size(), alt_img)
            self.status_download_files.config(
                text=f'Se han descargado {self.listbox.size()} de {self.imgs_length} imagenes',
                bg=bg_color)
            self.progress_bar.config(value=self.listbox.size() * 100 / self.imgs_length)
        except:
            print(img['src'] + " No ha podido ser descargada correctamente")

    def download_completed(self):
        self.status_download_files.configure(text=f'Descarga finalizada de las {self.imgs_length} imagenes')
        self.progress_bar.grid_forget()

    def observe_search_button(self):
        self.initialize_flow_download()
        self.observable_search_button(self.search.get()).subscribe(on_completed=self.download_completed)

    # END SECTION OBSERVABLE DOWNLOAD URL IMAGES

    # START SECTION OBSERVABLE LISTBOX
    def observable_select_item(self, widget, index):
        def search_item(o, s):
            try:
                img_key = f'{widget.get(index)}_{index}'
                aux_image = resize_image(self.imgs[img_key], "bytes")
                self.img_selected = ImageTk.PhotoImage(aux_image)
                self.canvas.create_image(20, 20, anchor=NW, image=self.img_selected)
            except:
                aux_image = resize_image("./assets/imgs/default.jpg", "file")
                self.img_selected = ImageTk.PhotoImage(aux_image)
                self.canvas.create_image(20, 20, anchor=NW, image=self.img_selected)
            o.on_completed()

        return create(search_item)

    def item_load_completed(self):
        print("Imagen cargada correctamente")

    def observe_select_item(self, event):
        self.observable_select_item(event.widget, event.widget.curselection()[0]) \
            .subscribe(on_completed=self.item_load_completed)

    # END SECTION OBSERVABLE LISTBOX


if __name__ == '__main__':
    async_loop = asyncio.get_event_loop()
    App(async_loop)
