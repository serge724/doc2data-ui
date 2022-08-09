import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory, askopenfilename, asksaveasfilename
from state import State
from doc2data.pdf import PDFCollection

# ...
class FileControl(ttk.LabelFrame):

    def __init__(self, master, state, *args, **kwargs):
        super().__init__(master, text = 'File controls', *args, **kwargs)

        self.state = state

        # register callback if new file selected
        self.state.file_selected_idx.trace_add('write', self.on_file_change)

        # loading and saving of pdf_collection
        frm_io = ttk.Frame(self)
        btn_create_collection = ttk.Button(
            master = frm_io,
            text = 'Create collection',
            command = self.create_collection
        )
        btn_create_collection.pack(side = 'left', padx = 2, pady = 2)
        btn_load_collection = ttk.Button(
            master = frm_io,
            text = 'Load collection',
            command = self.load_collection
        )
        btn_load_collection.pack(side = 'left', padx = 2, pady = 2)
        btn_save_collection = ttk.Button(
            master = frm_io,
            text = 'Save collection',
            command = self.save_collection
        )
        btn_save_collection.pack(side = 'left', padx = 2, pady = 2)
        frm_io.pack(side = 'top')

        # info on PDF collection
        frm_collection_info = ttk.Frame(self)
        lbl_collection_path_key = ttk.Label(frm_collection_info, text = 'Path to collection:')
        lbl_collection_path_key.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'w')
        self.lbl_collection_path_value = ttk.Label(frm_collection_info, text = 'Collection not saved.')
        if hasattr(self.state.pdf_collection, 'path_to_collection'):
            self.lbl_collection_path_value = ttk.Label(frm_collection_info, text = os.path.basename(self.state.pdf_collection.path_to_collection))
        self.lbl_collection_path_value.grid(row = 0, column = 1, padx = 2, pady = 2, sticky = 'w')
        lbl_document_path_key = ttk.Label(frm_collection_info, text = 'Path to documents:')
        lbl_document_path_key.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'w')
        self.lbl_document_path_value = ttk.Label(frm_collection_info, text = os.path.basename(self.state.pdf_collection.path_to_files))
        self.lbl_document_path_value.grid(row = 1, column = 1, padx = 2, pady = 2, sticky = 'w')
        lbl_n_files_key = ttk.Label(frm_collection_info, text = 'Number of files:')
        lbl_n_files_key.grid(row = 2, column = 0, padx = 2, pady = 2, sticky = 'w')
        self.lbl_n_files_value = ttk.Label(frm_collection_info, text = self.state.pdf_collection.n_files)
        self.lbl_n_files_value.grid(row = 2, column = 1, padx = 2, pady = 2, sticky = 'w')
        frm_collection_info.pack(side = 'top')

        # file selection
        frm_file_selection = ttk.Frame(self)
        frm_file_selection.columnconfigure(0, weight = 1)
        btn_previous_file = ttk.Button(
            master = frm_file_selection,
            text = 'Previous file',
            command = self.load_previous_file
        )
        btn_previous_file.pack(side = 'left', padx = 2, pady = 2)
        btn_next_file = ttk.Button(
            master = frm_file_selection,
            text = 'Next file',
            command = self.load_next_file
        )
        btn_next_file.pack(side = 'left', padx = 2, pady = 2)
        frm_file_selection.pack(side = 'top')

        # file info
        frm_file_info = ttk.Frame(self)
        lbl_file_name_key = ttk.Label(frm_file_info, text = 'File name:')
        lbl_file_name_key.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'w')
        self.lbl_file_name_value = ttk.Label(frm_file_info, text = 'None')
        self.lbl_file_name_value.grid(row = 0, column = 1, padx = 2, pady = 2, sticky = 'w')
        lbl_file_idx_key = ttk.Label(frm_file_info, text = 'File number:')
        lbl_file_idx_key.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'w')
        self.lbl_file_idx_value = ttk.Label(frm_file_info, text = None)
        self.lbl_file_idx_value.grid(row = 1, column = 1, padx = 2, pady = 2, sticky = 'w')
        frm_file_info.pack(side = 'top')

        # bind events
        self._root().bind('y', lambda event: self.load_previous_file())
        self._root().bind('x', lambda event: self.load_next_file())

        # debug
        debug = True
        if debug:
            frm_debug = ttk.Frame(self)
            btn_reset_collection = ttk.Button(frm_debug, text = 'Debug: Reset all', command = self.reset_pdf_collection)
            btn_reset_collection.pack(side = 'left', padx = 2, pady = 2)
            btn_state_display = ttk.Button(frm_debug, text = 'Debug: state info', command = self.debug_print_state)
            btn_state_display.pack(side = 'left', padx = 2, pady = 2)
            frm_debug.pack(side = 'top')

            self._root().bind('<Alt_L>', lambda event: self.debug_print_state())

    def load_next_file(self):

        if self.state.file_selected_idx.get() < self.state.pdf_collection.n_files - 1:
            self.state.file_selected_idx.set(self.state.file_selected_idx.get() + 1)

    def load_previous_file(self):

        if self.state.file_selected_idx.get() > 0:
            self.state.file_selected_idx.set(self.state.file_selected_idx.get() - 1)

    def on_file_change(self, *args):

        idx = self.state.file_selected_idx.get()
        n_files = self.state.pdf_collection.n_files
        file_name, file = self.state.indexed_files[idx]
        self.lbl_file_name_value.config(text = file_name)
        self.lbl_file_idx_value.config(text = '%s / %s'%(idx + 1, n_files))

    def create_collection(self):

        path_to_pdfs = askdirectory()
        pdf_collection = PDFCollection(path_to_files = path_to_pdfs)
        self.state.reset(pdf_collection, self.state.bbox_label_dict)

        self.lbl_document_path_value.config(text = os.path.basename(path_to_pdfs))
        self.lbl_n_files_value.config(text = pdf_collection.n_files)

    def load_collection(self):

        path_to_collection = askopenfilename()
        pdf_collection = PDFCollection.load(path_to_collection)
        self.state.reset(pdf_collection, self.state.bbox_label_dict)

        self.lbl_document_path_value.config(text = os.path.basename(pdf_collection.path_to_files))
        self.lbl_collection_path_value.config(text = os.path.basename(pdf_collection.path_to_collection))
        self.lbl_n_files_value.config(text = pdf_collection.n_files)

    def save_collection(self):

        dir_name = 'saved'
        os.makedirs(dir_name, exist_ok = True)
        path_to_collection = asksaveasfilename()
        self.state.pdf_collection.path_to_collection = path_to_collection
        self.state.pdf_collection.save(path_to_collection, overwrite = True)
        self.lbl_collection_path_value.config(text = os.path.basename(path_to_collection))

    def reset_pdf_collection(self):

        pdf_collection = PDFCollection(self.state.pdf_collection.path_to_files)
        pdf_collection.save('db/pdf_collection.pickle', overwrite = True)
        self._root().destroy()

    def debug_print_state(self):
        if not hasattr(self, 'state_count'):
            self.state_count = 0

        self.state_count += 1
        print('                                Count: %s'%(self.state_count))
        print('#########################\n# INTERNAL STATE\n#########################')
        for k, v in self.state.__dict__.items():
            if k == 'indexed_files':
                print(k, ':', '...')
            elif k == 'file_selected_idx' or k == 'page_edit_mode' or k == 'page_bbox_label_idx':
                print(k, ':', v.get())
            elif k == 'page_token_bboxes':
                if v is not None:
                    print(k, ':', list(v.items())[0])
                else:
                    print(k, ':')
            else:
                print(k, ':', v)
        print('#########################\n# PAGE LABELS\n#########################')
        for k, v in self.state.page.labels.__dict__.items():
            if k == 'tokens':
                if v is not None:
                    print(k, ':', v[0])
                else:
                    print(k, ':')
            else:
                print(k, ':', v)
        print('#########################')
        # for i in self.state.page.labels.tokens:
        #     print(i)

# ...
class PageControl(ttk.LabelFrame):

    def __init__(self, master, state, page_analysis, *args, **kwargs):
        super().__init__(master, text = 'Document controls', *args, **kwargs)

        self.state = state
        self.page_analysis = page_analysis
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 1)

        self.frm_mode_control = ttk.Frame(self)
        rbtn_preprocessing_mode = ttk.Radiobutton(
            self.frm_mode_control,
            name = 'rbtn_preprocessing_mode',
            text = 'Preprocessing',
            variable = self.state.page_edit_mode,
            value = 'preprocessing',
            width = 15
        )
        rbtn_preprocessing_mode.pack(side = 'top', anchor = 'w', padx = 2, pady = 2)
        rbtn_ocr_mode = ttk.Radiobutton(
            self.frm_mode_control,
            name = 'rbtn_ocr_mode',
            text = 'OCR',
            variable = self.state.page_edit_mode,
            value = 'ocr',
            width = 15
        )
        rbtn_ocr_mode.pack(side = 'top', anchor = 'w', padx = 2, pady = 2)
        rbtn_drawing_mode = ttk.Radiobutton(
            self.frm_mode_control,
            name = 'rbtn_drawing_mode',
            text = 'Drawing',
            variable = self.state.page_edit_mode,
            value = 'drawing',
            width = 15
        )
        rbtn_drawing_mode.pack(side = 'top', anchor = 'w', padx = 2, pady = 2)
        self.frm_mode_control.grid(row = 0, column = 0, sticky = 'e')

        frm_controls = ttk.Frame(self)
        btn_rotate_left = ttk.Button(
            master = frm_controls,
            text = 'Rotation -90°',
            command = lambda: self.page_analysis.rotate(90)
        )
        btn_rotate_left.grid(row = 0, column = 0, padx = 2, pady = 2)
        btn_rotate_right = ttk.Button(
            master = frm_controls,
            text = 'Rotation +90°',
            command = lambda: self.page_analysis.rotate(-90)
        )
        btn_rotate_right.grid(row = 0, column = 1, padx = 2, pady = 2)
        btn_apply_crop = ttk.Button(
            master = frm_controls,
            text = 'Crop',
            command = self.page_analysis.define_crop_bbox
        )
        btn_apply_crop.grid(row = 1, column = 0, padx = 2, pady = 2)
        btn_run_ocr = ttk.Button(
            master = frm_controls,
            text = 'Run OCR',
            command = self.page_analysis.run_ocr
        )
        btn_run_ocr.grid(row = 1, column = 1, padx = 2, pady = 2)
        btn_reload = ttk.Button(
            master = frm_controls,
            text = 'Reset',
            command = self.page_analysis.reset
        )
        btn_reload.grid(row = 2, column = 0, columnspan = 2, padx = 2, pady = 2)
        frm_controls.grid(row = 0, column = 1, sticky = 'w')
