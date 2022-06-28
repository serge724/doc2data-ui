import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog

from PIL import Image, ImageTk
from pdf2image import convert_from_path

import functions
import Pmw


class StartWindow:

    def __init__(self, master):
        self.master = master

        self.configure_master()
        self.configure_frame()

    # CONFIGURE UI ELEMENTS
    def configure_master(self):
        self.master.title("doc2data")
        self.master.resizable(False, False)

    def configure_frame(self):
        tk.Message(self.master, text="Welcome to doc2data!", width=200, justify=tk.CENTER).pack(padx=20, pady=(20, 5))
        tk.Message(self.master, text="Do you want to create a new database from or load existing database?", width=250,
                   justify=tk.CENTER).pack(padx=20, pady=(5, 5))
        buttons = ttk.Frame(self.master)
        ttk.Button(buttons, text="Create Database", command=self.create_database).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Load Database", command=self.load_database).pack(side=tk.RIGHT)
        buttons.pack(padx=20, pady=(5, 20))

    # DEFINE UI FUNCTIONS
    def create_database(self):
        path = filedialog.askdirectory()
        # TODO: Create database from path and pass it on
        main_window = tk.Toplevel(self.master)
        MainWindow(main_window, None)
        self.master.withdraw()

    def load_database(self):
        print("loaded")


class MainWindow:

    def __init__(self, master, database):
        self.master = master
        self.style = ttk.Style()

        self.database = database

        self.configure_master()
        self.configure_menu_bar()
        self.configure_notebook()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    # CONFIGURE UI ELEMENTS
    def configure_master(self):
        self.master.title("doc2data")

    def configure_menu_bar(self):
        menubar = tk.Menu(self.master)

        ## Filemenu
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Database", menu=filemenu)
        filemenu.add_command(label="Save", command=lambda: print("Save"))  # TODO
        filemenu.add_command(label="Open", command=self.new_database)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)

        self.master.configure(menu=menubar)

    def configure_notebook(self):
        self.notebook = ttk.Notebook(self.master)

        self.configure_file_tab()
        self.configure_document_tab()
        self.configure_content_tab()

        self.notebook.add(self.file_tab, text="Files")
        self.notebook.add(self.document_tab, text="Documents")
        self.notebook.add(self.content_tab, text="Content")

        self.notebook.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # file tab
    def configure_file_tab(self):
        self.file_tab = ttk.Frame(self.notebook)

        self.configure_file_preview()
        self.configure_file_info()
        self.configure_file_functions()

    def configure_file_preview(self):
        self.file_preview = ttk.Frame(self.file_tab)

        file_canvas_width = 400
        self.file_canvas = tk.Canvas(self.file_preview, width=file_canvas_width, height=1.414214 * file_canvas_width)

        # Test PDF
        file_image = convert_from_path("example_docs/241953.pdf")[0]
        print(file_image)
        file_image.thumbnail((file_canvas_width, 1.414214 * file_canvas_width))
        image = ImageTk.PhotoImage(file_image)

        self.file_canvas.create_image(0, 0, image=image, anchor='nw')
        self.file_canvas.image = image  # by bug

        self.file_canvas.pack(anchor=tk.CENTER)

        self.file_preview.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_file_info(self):
        self.file_info = ttk.Frame(self.file_tab)

        ttk.Label(self.file_info, text="Here will be information about the file").pack(padx=30, pady=30)
        ttk.Label(self.file_info, text="General Information:\nName: 167732.pdf\nPages: 1\n...").pack(padx=30, pady=30)

        ttk.Separator(self.file_info, orient='horizontal').pack(padx=20, fill="x")

        self.lbl_file_info = ttk.Label(self.file_info,
                  text="List of Documents in this File:\n- Rechnung (Page 1)\n- Nachweis (Page 2-3)")
        self.lbl_file_info.pack(padx=30, pady=30)

        self.file_info.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_file_functions(self):
        self.file_functions = ttk.Frame(self.file_tab)

        self.configure_file_functions_general()
        ttk.Separator(self.file_functions, orient='horizontal').pack(padx=20, fill="x")
        self.configure_file_functions_label()

        self.file_functions.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_file_functions_general(self):
        self.file_functions_general = ttk.Frame(self.file_functions)

        ttk.Button(self.file_functions_general, text="Add File").pack(padx=10, pady=10)
        ttk.Button(self.file_functions_general, text="Delete File").pack(padx=10, pady=10)
        ttk.Button(self.file_functions_general, text="Previous File").pack(padx=10, pady=(30, 10))
        ttk.Button(self.file_functions_general, text="Next File").pack(padx=10, pady=10)
        ttk.Label(self.file_functions_general, text="Open File:\n344722.pdf\n224454.pdf\n...").pack(padx=10, pady=10)

        self.file_functions_general.pack(padx=20, pady=20)

    def configure_file_functions_label(self):
        self.file_functions_label = ttk.Frame(self.file_functions)

        ttk.Label(self.file_functions_label, text="Label Document").grid(row=0, columnspan=4)
        ttk.Label(self.file_functions_label, text="First Page:").grid(row=1, column=0)
        ttk.Entry(self.file_functions_label, width=10).grid(row=1, column=1)
        ttk.Label(self.file_functions_label, text="Last Page:").grid(row=1, column=2)
        ttk.Entry(self.file_functions_label, width=10).grid(row=1, column=3)
        document_type_combobox = ttk.Combobox(self.file_functions_label)
        document_type_combobox["values"] = ("Rechnung", "Nachweis", "Ausweis")
        document_type_combobox["state"] = "readonly"
        document_type_combobox.grid(row=2, columnspan=4)
        ttk.Button(self.file_functions_label, text="Add", command=self.add).grid(row=3, columnspan=4)

        self.file_functions_label.pack(padx=20, pady=20)

    def add(self):
        self.lbl_file_info.text = "Test"  # doesn't work, do we need StringVar()?


    # document tab
    def configure_document_tab(self):
        self.document_tab = ttk.Frame(self.notebook)

        self.configure_document_preview()
        self.configure_document_info()
        self.configure_document_functions()

    def configure_document_preview(self):
        self.document_preview = ttk.Frame(self.document_tab)

        ttk.Label(self.document_preview, text="Here will be the pdf of the document").pack(padx=30, pady=30)

        self.document_preview.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_document_info(self):
        self.style.configure("green_frame.TFrame", background="green")

        self.document_info = ttk.Frame(self.document_tab, style="green_frame.TFrame")

        ttk.Label(self.document_info, text="Here will be information about the document").pack(padx=30, pady=30)

        self.document_info.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_document_functions(self):
        self.document_functions = ttk.Frame(self.document_tab)

        ttk.Label(self.document_functions,
                  text="Here will be buttons, comboboxes, etc. to work with the document").pack(padx=30, pady=30)

        self.document_functions.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    # content tab
    def configure_content_tab(self):
        self.content_tab = ttk.Frame(self.notebook)

        self.configure_content_preview()
        self.configure_content_info()
        self.configure_content_functions()

    def configure_content_preview(self):
        self.content_preview = ttk.Frame(self.content_tab)

        ttk.Label(self.content_preview, text="Here will be the pdf of the content").pack(padx=30, pady=30)

        self.content_preview.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_content_info(self):
        self.style.configure("yellow_frame.TFrame", background="yellow")

        self.content_info = ttk.Frame(self.content_tab, style="yellow_frame.TFrame")

        ttk.Label(self.content_info, text="Here will be information about the content").pack(padx=30, pady=30)

        self.content_info.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def configure_content_functions(self):
        self.content_functions = ttk.Frame(self.content_tab)

        ttk.Label(self.content_functions,
                  text="Here will be buttons, comboboxes, etc. to work with the content").pack(padx=30, pady=30)

        self.content_functions.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    # DEFINE UI FUNCTIONS
    def on_closing(self):
        self.master.quit()

    def new_database(self):
        start_window = tk.Toplevel(self.master)
        StartWindow(start_window)
        self.master.withdraw()


# run application
if __name__ == '__main__':
    root = tk.Tk()
    app = StartWindow(root)
    root.mainloop()
