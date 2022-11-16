import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory, askopenfilename, asksaveasfilename
from tkinter.simpledialog import SimpleDialog
from datetime import datetime
from components.state import State, PageLabels
from components.canvas import PageCanvas, BoundingBox
from components.ocr import run_doctr_ocr
from doc2data.utils import denormalize_bbox
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
        lbl_n_pdfs_key = ttk.Label(frm_collection_info, text = 'Number of files:')
        lbl_n_pdfs_key.grid(row = 2, column = 0, padx = 2, pady = 2, sticky = 'w')
        self.lbl_n_pdfs_value = ttk.Label(frm_collection_info, text = len(self.state.pdf_collection.pdfs))
        self.lbl_n_pdfs_value.grid(row = 2, column = 1, padx = 2, pady = 2, sticky = 'w')
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
        self.btn_next_file = ttk.Button(
            master = frm_file_selection,
            text = 'Next file',
            command = self.load_next_file
        )
        self.btn_next_file.pack(side = 'left', padx = 2, pady = 2)
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

        # add button to delete documents and close app
        self.btn_finish_session = ttk.Button(self, text = 'Finish session', state = 'disabled', command = self.finish_session)
        self.btn_finish_session.pack(side = 'top', padx = 2, pady = 2)

        # debug
        debug = False
        if debug:
            frm_debug = ttk.Frame(self)
            btn_reset_collection = ttk.Button(frm_debug, text = 'Debug: Reset all', command = self.reset_pdf_collection)
            btn_reset_collection.pack(side = 'left', padx = 2, pady = 2)
            btn_state_display = ttk.Button(frm_debug, text = 'Debug: state info', command = self.debug_print_state)
            btn_state_display.pack(side = 'left', padx = 2, pady = 2)
            frm_debug.pack(side = 'top')

            self._root().bind('<Alt_L>', lambda event: self.debug_print_state())

    def load_next_file(self):

        if self.state.file_selected_idx.get() < len(self.state.pdf_collection.pdfs) - 1:
            self.state.file_selected_idx.set(self.state.file_selected_idx.get() + 1)

    def load_previous_file(self):

        if self.state.file_selected_idx.get() > 0:
            self.state.file_selected_idx.set(self.state.file_selected_idx.get() - 1)

    def on_file_change(self, *args):

        idx = self.state.file_selected_idx.get()
        n_pdfs = len(self.state.pdf_collection.pdfs)
        file_name, file = self.state.indexed_files[idx]
        self.lbl_file_name_value.config(text = file_name)
        self.lbl_file_idx_value.config(text = '%s / %s'%(idx + 1, n_pdfs))

        # check if btn_next_file should be enabled
        if not self.state.page.labels.confirmed:
            self.btn_next_file['state'] = 'disabled'
            self._root().unbind('x')
        else:
            self.btn_next_file['state'] = 'normal'
            self._root().bind('x', lambda event: self.load_next_file())

    def create_collection(self):

        path_to_pdfs = askdirectory()
        pdf_collection = PDFCollection(path_to_files = path_to_pdfs)
        self.state.reset(pdf_collection, self.state.bbox_label_dict)

        self.lbl_document_path_value.config(text = os.path.basename(path_to_pdfs))
        self.lbl_n_pdfs_value.config(text = len(pdf_collection.pdfs))

    def load_collection(self):

        path_to_collection = askopenfilename()
        pdf_collection = PDFCollection.load(path_to_collection)
        self.state.reset(pdf_collection, self.state.bbox_label_dict)

        self.lbl_document_path_value.config(text = os.path.basename(pdf_collection.path_to_files))
        self.lbl_collection_path_value.config(text = os.path.basename(pdf_collection.path_to_collection))
        self.lbl_n_pdfs_value.config(text = len(pdf_collection.pdfs))

    def save_collection(self):

        dir_name = 'saved'
        os.makedirs(dir_name, exist_ok = True)
        path_to_collection = asksaveasfilename()
        self.state.pdf_collection.path_to_collection = path_to_collection
        self.state.pdf_collection.save(path_to_collection, overwrite = True)
        self.lbl_collection_path_value.config(text = os.path.basename(path_to_collection))

    def reset_pdf_collection(self):

        pdf_collection = PDFCollection(self.state.pdf_collection.path_to_files)
        pdf_collection.save('tmp/last_collection.pickle', overwrite = True)
        self._root().destroy()

    def finish_session(self):

        os.makedirs('labels', exist_ok = True)
        self.state.pdf_collection.save(f'labels/submission_{datetime.today().strftime("%Y-%m-%d_%H-%M-%S")}.pickle', overwrite = False)

        path = self.state.pdf_collection.path_to_files
        files = os.listdir(path)
        for i in files: os.remove(os.path.join(path, i))
        os.remove('tmp/last_collection.pickle')
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


# ...
class PageLevelProcessing(ttk.Frame):

    def __init__(self, master, state, file_control, only_values, hsn_df, tsn_df, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # attach state and callbacks
        self.state = state
        self.state.file_selected_idx.trace_add('write', self.on_file_change)
        self.state.page_edit_mode.trace_add('write', self.on_mode_change)
        self.delay = 1

        # define ui components
        self.canvas = PageCanvas(master, state, bg = 'gray')
        self.control = PageControl(master, state, self, relief = 'groove', borderwidth = 3)
        self.bbox_label_control = BboxLabelControl(master, state, self, file_control, only_values, hsn_df, tsn_df, relief = 'groove', borderwidth = 3)

        # initiate variable attributes
        self.processed_image = None
        self.page_is_cropped = None

        # bind events
        self._root().bind('<Prior>', lambda event: self.rotate(90))
        self._root().bind('<Next>', lambda event: self.rotate(-90))
        self._root().bind('c', lambda event: self.define_crop_bbox())
        self._root().bind('r', lambda event: self.run_ocr())
        self._root().bind('s', lambda event: self.save_bounding_box())
        self._root().bind('b', lambda event: self.bbox_label_control.switch_label('previous'))
        self._root().bind('n', lambda event: self.bbox_label_control.switch_label('next'))

    # removes all objects on canvas and creates new image
    def update_canvas(self):

        displayed_image = self.processed_image.copy()
        self.canvas.delete('all')
        self.canvas.create_image(displayed_image)

    # loads new page and initiates labels
    def load_page(self):

        if not hasattr(self.state.page, 'labels'):
            self.state.page.labels = PageLabels(0, None, None, None, False)
        self.processed_image = self.state.page.read_contents('page_image', dpi = 100, force_rgb = True)
        self.state.page_is_cropped = False

        w, h = self.processed_image.size
        canvas_frame_width = self.canvas.frm_container.winfo_width()
        canvas_frame_height = self.canvas.frm_container.winfo_height()
        zoom = min((canvas_frame_width / w, canvas_frame_height / h))
        self.processed_image = self.processed_image.resize((int(w*zoom), int(h*zoom)))

        self.update_canvas()

        print('page loaded')

    # rotates page
    def rotate(self, angle, set_label = True):

        self.processed_image = self.processed_image.rotate(angle, expand = 1)
        if set_label: self.state.page.labels.rotation += angle
        self.update_canvas()
        print('page rotated.')

    # defines crop box from labels or annotation
    def define_crop_bbox(self, set_label = True):
        # load crop bbox that is present in labels
        if not set_label:
            if self.state.page.labels.crop_bbox is not None:
                denormalized_coords = denormalize_bbox(self.state.page.labels.crop_bbox, self.canvas.tk_image.width(), self.canvas.tk_image.height())
                self.canvas.set_crop_box(denormalized_coords)
        # apply crop bbox that was drawn
        else:
            if self.state.page_crop_bbox is not None:
                crop_bbox = self.state.page_crop_bbox
                self.state.page.labels.crop_bbox = crop_bbox.normalized_coords
                self.state.page_edit_mode.set('ocr')
        print('crop bbox defined.')

    # creates tokens with bboxes from labels or OCR
    def run_ocr(self, set_label = True):

        self.state.page_token_bboxes = dict()

        if not set_label:
            for i, t in self.state.page.labels.tokens.items():
                denormalized_coords = denormalize_bbox(t['bbox'], self.canvas.tk_image.width(), self.canvas.tk_image.height())
                bbox = BoundingBox(master_canvas = self.canvas, type = t['type'], token_id = t['id'])
                bbox.draw_rectangle(denormalized_coords)
                bbox.text = t['word']
                if 'label' in t:
                    bbox.set_label(t['label'])
                self.state.page_token_bboxes[bbox.rectangle_id] = bbox
                self.canvas.tag_bind(bbox.rectangle_id, '<Button-1>', lambda event: self.state.page_token_bboxes[event.widget.find_withtag('current')[0]].on_click())
            print('ocr tokens loaded')
        else:
            if self.state.page.labels.tokens is None:
                self.state.page_edit_mode.set('ocr')
                ocr_tokens = run_doctr_ocr(self.processed_image)
                ocr_tokens_dict = {k: v for k, v in enumerate(ocr_tokens)}
                self.state.page.labels.tokens = ocr_tokens_dict
                for i, t in self.state.page.labels.tokens.items():
                    denormalized_coords = denormalize_bbox(t['bbox'], self.canvas.tk_image.width(), self.canvas.tk_image.height())
                    bbox = BoundingBox(master_canvas = self.canvas, type = t['type'], token_id = t['id'])
                    bbox.draw_rectangle(denormalized_coords)
                    bbox.text = t['word']
                    self.state.page_token_bboxes[bbox.rectangle_id] = bbox
                    self.canvas.tag_bind(bbox.rectangle_id, '<Button-1>', lambda event: self.state.page_token_bboxes[event.widget.find_withtag('current')[0]].on_click())
                print('ocr tokens generated')

    # callback that handles change of pages
    def on_file_change(self, *args):
        print('on_file_change')

        # save current file index and label data if new file is selected
        self.state.pdf_collection.file_selected_idx = self.state.file_selected_idx.get()
        self.state.pdf_collection.save('tmp/last_collection.pickle', overwrite = True)

        # select new file and page
        file_name, file = self.state.indexed_files[self.state.file_selected_idx.get()]
        self.state.page = file.parsed_pages[0]

        # reset bbox_label_control
        self.bbox_label_control.clear_ent_widgets()

        # set state of the app according to available labels
        self.state.page_edit_mode.set('preprocessing')
        self.state.page_bbox_label_idx.set(0)
        if self.state.page.labels.crop_bbox is not None:
            self.after(900 * self.delay, lambda: self.state.page_edit_mode.set('ocr'))
        if self.state.page.labels.tokens is not None:
            self.after(900 * self.delay, lambda: self.state.page_edit_mode.set('ocr'))

        # ...
        if os.path.exists('upload.json'):
            os.remove('upload.json')
            self.bbox_label_control.lbl_hsn_value.config(text = "")
            self.bbox_label_control.lbl_tsn_value.config(text = "")

        # save results should be deactivated every time file changes to ensure values are checked
        self.bbox_label_control.btn_update_key_text['state'] = 'disabled'

    # callback that handels change of edit mode
    def on_mode_change(self, *args):

        # preprocessing mode
        if self.state.page_edit_mode.get() == 'preprocessing':

            print('preprocessing mode')
            self.load_page()

            # rotate if rotation label exists
            if self.state.page.labels.rotation != 0:
                self.after(300 * self.delay, lambda: self.rotate(self.state.page.labels.rotation, set_label = False))
            # draw crop bbox if label exists
            if self.state.page.labels.crop_bbox is not None:
                self.after(600 * self.delay, lambda: self.define_crop_bbox(set_label = False))

        # ocr token selection mode
        elif self.state.page_edit_mode.get() == 'ocr':
            print('ocr mode')
            # apply cropping if crop box was defined
            if self.state.page.labels.crop_bbox is not None and not self.state.page_is_cropped:
                crop_bbox = self.state.page_crop_bbox
                coords = list([crop_bbox.start_x, crop_bbox.start_y, crop_bbox.end_x, crop_bbox.end_y])
                self.processed_image = self.processed_image.crop(coords)
                # zoom if cropped image is small
                w, h = self.processed_image.size
                canvas_frame_width = self.canvas.frm_container.winfo_width()
                canvas_frame_height = self.canvas.frm_container.winfo_height()
                zoom = min((canvas_frame_width / w, canvas_frame_height / h))
                self.processed_image = self.processed_image.resize((int(w*zoom), int(h*zoom)))
                # update state
                self.state.page_is_cropped = True
                crop_bbox.destroy()
                self.update_canvas()
            else:
                w, h = self.processed_image.size
                canvas_frame_width = self.canvas.winfo_width()
                canvas_frame_height = self.canvas.winfo_height()
                zoom = min((canvas_frame_width / w, canvas_frame_height / h))
                self.processed_image = self.processed_image.resize((int(w*zoom), int(h*zoom)))
                self.update_canvas()

            # load tokens if ocr labels exist
            if self.state.page.labels.tokens is not None:
                self.after(300 * self.delay, lambda: self.run_ocr(set_label = False))

            if self.state.page.labels.key_values is not None:
                self.after(600 * self.delay, lambda: self.bbox_label_control.extract_text(set_label = False))

        # bbox drawing mode
        elif self.state.page_edit_mode.get() == 'drawing':
            print('drawing mode')

    # resets all page labels
    def reset(self):
        file_name, file = self.state.indexed_files[self.state.file_selected_idx.get()]
        self.state.page = file.parsed_pages[0]

        # ...
        self.state.page.labels = PageLabels(0, None, None, None, False)

        # reset bbox_label_control
        self.bbox_label_control.clear_ent_widgets()

        # set state of the app according to available labels
        self.state.page_edit_mode.set('preprocessing')
        self.state.page_bbox_label_idx.set(0)

    # ...
    def save_bounding_box(self):

        print('bbox saved')
        if self.state.page_edit_mode.get() == 'drawing':
            if self.state.page_drawn_bbox is not None:
                bbox = self.state.page_drawn_bbox
                image = bbox.get_image_segment()
                segment_tokens = run_doctr_ocr(image)
                joined_token = ' '.join([i['word'] for i in segment_tokens])

                # ...
                self.state.page_token_bboxes[bbox.rectangle_id] = bbox

                # ...
                last_token_id = list(self.state.page.labels.tokens.keys())[-1] if self.state.page.labels.tokens is not None else -1

                # complete information in bbox object
                bbox.text = joined_token
                bbox.token_id = last_token_id + 1

                self.state.page.labels.tokens[bbox.token_id] = {
                    'id': bbox.token_id,
                    'bbox': bbox.get_normalized_coords(),
                    'word': bbox.text,
                    'type': 'user',
                    'timestamp': datetime.now().__str__()
                }

                self.state.page_drawn_bbox.on_click()
                self.canvas.tag_bind(bbox.rectangle_id, '<Button-1>', lambda event: bbox.on_click())

                # move to next label key
                self.bbox_label_control.switch_label('next')


# ...
def validate(date_text):
    try:
        datetime.strptime(date_text, '%d.%m.%Y')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY.MM.DD")



class BboxLabelControl(ttk.LabelFrame):

    def __init__(self, master, state, page_analysis, file_control, only_values, hsn_df, tsn_df, *args, **kwargs):
        super().__init__(master, text = 'Labeling', *args, **kwargs)

        # attach state and link parent component
        self.state = state
        self.page_analysis = page_analysis
        self.file_control = file_control
        self.hsn_df = hsn_df
        self.tsn_df = tsn_df

        self.style = ttk.Style(self)
        self.style.configure('TButton', width = 15)

        # define ui components
        frm_labeling_control = ttk.Frame(self)
        btn_prev_label = ttk.Button(
            master = frm_labeling_control,
            text = 'Previous label',
            command = lambda: self.switch_label('previous')
        )
        btn_prev_label.grid(row = 0, column = 0, padx = 2, pady = 2)
        btn_next_label = ttk.Button(
            master = frm_labeling_control,
            text = 'Next label',
            command = lambda: self.switch_label('next')
        )
        btn_next_label.grid(row = 0, column = 1, padx = 2, pady = 2)
        btn_save_bbox = ttk.Button(
            master = frm_labeling_control,
            text = 'Save box',
            command = self.page_analysis.save_bounding_box
        )
        btn_save_bbox.grid(row = 1, column = 0, padx = 2, pady = 2)
        btn_extract_text = ttk.Button(
            master = frm_labeling_control,
            text = 'Extract text',
            command = self.extract_text
        )
        btn_extract_text.grid(row = 1, padx = 2, column = 1, pady = 2)
        frm_labeling_control.pack(side = 'top')

        frm_bbox_labeling = ttk.Frame(self)
        if only_values:
            self.state.page_bbox_text_entry = {}
            for k, v in self.state.pdf_collection.bbox_label_dict.items():
                lbl_label_key = tk.Label(frm_bbox_labeling, text = '%s: %s'%(k, v))
                lbl_label_key.grid(column = 0, row = k, sticky = 'w')
                bbox_text = tk.StringVar()
                ent_bbox_text = ttk.Entry(frm_bbox_labeling, textvariable = bbox_text)
                ent_bbox_text.grid(column = 1, row = k, sticky = 'w')
                self.state.page_bbox_text_entry[k] = {'lbl_widget': lbl_label_key, 'string_var': bbox_text}
        else:
            self.state.page_bbox_text_entry = {}
            row = 0
            for k, v in self.state.pdf_collection.bbox_label_dict.items():
                if 'key' in v:
                    key_name = v.split('_')[0]
                    lbl_label_key_name = ttk.Label(frm_bbox_labeling, text = '%s:'%key_name)
                    lbl_label_key_name.grid(column = 0, row = row, sticky = 'w')
                    lbl_label_key_idx = ttk.Label(frm_bbox_labeling, text = k)
                    lbl_label_key_idx.grid(column = 1, row = row, sticky = 'e')
                    bbox_text = tk.StringVar()
                    ent_bbox_text = ttk.Entry(frm_bbox_labeling, textvariable = bbox_text)
                    ent_bbox_text.grid(column = 2, row = row, sticky = 'w')
                    self.state.page_bbox_text_entry[k] = {'lbl_widget': lbl_label_key_idx, 'string_var': bbox_text}
                if 'value' in v:
                    lbl_label_value_idx = ttk.Label(frm_bbox_labeling, text = k)
                    lbl_label_value_idx.grid(column = 3, row = row, sticky = 'e')
                    bbox_text = tk.StringVar()
                    ent_bbox_text = ttk.Entry(frm_bbox_labeling, textvariable = bbox_text)
                    ent_bbox_text.grid(column = 4, row = row, sticky = 'w')
                    self.state.page_bbox_text_entry[k] = {'lbl_widget': lbl_label_value_idx, 'string_var': bbox_text}
                    row += 1

        frm_bbox_labeling.pack(side = 'top', pady = 20)

        frm_value_check = ttk.Frame(self)
        btn_check_values = ttk.Button(
            master = frm_value_check,
            text = 'Check values',
            command = self.check_values
        )
        btn_check_values.grid(row = 0, column = 0, columnspan = 1, rowspan = 2, padx = 2, pady = 2)
        lbl_hsn_key = ttk.Label(frm_value_check, text = 'HSN:')
        lbl_hsn_key.grid(row = 0, column = 1, padx = 2, pady = 2)
        self.lbl_hsn_value = ttk.Label(frm_value_check, text = '')
        self.lbl_hsn_value.grid(row = 0, column = 2, padx = 2, pady = 2)
        lbl_tsn_key = ttk.Label(frm_value_check, text = 'TSN:')
        lbl_tsn_key.grid(row = 1, column = 1, padx = 2, pady = 2)
        self.lbl_tsn_value = ttk.Label(frm_value_check, text = '')
        self.lbl_tsn_value.grid(row = 1, column = 2, padx = 2, pady = 2)
        frm_value_check.pack(side = 'top', pady = 10, fill = "x", expand = True)

        frm_finish_file = ttk.Frame(self)
        self.btn_update_key_text = ttk.Button(
            master = frm_finish_file,
            text = 'Save result',
            command = self.update_key_text
        )
        self.btn_update_key_text.pack(side = 'left', padx = 2, pady = 2)
        self.btn_skip_file = ttk.Button(
            master = frm_finish_file,
            text = 'Skip file',
            command = self.skip_file
        )
        self.btn_skip_file.pack(side = 'left', padx = 2, pady = 2)
        frm_finish_file.pack(side = 'top', pady = 2)

        # temp
        self._root().bind('e', lambda event: self.extract_text())

    def skip_file(self):
        print('file skipped')

        # write results to json
        import json
        idx = self.state.file_selected_idx.get()
        file_name, _ = self.state.indexed_files[idx]
        json_result = {
            'file_name': file_name,
            'skipped': True
        }
        print(json_result)
        with open('upload.json', 'wt') as file:
            json.dump(json_result, file)

        self.state.page.labels.confirmed = True
        self.file_control.btn_next_file['state'] = 'normal'
        self._root().bind('x', lambda event: self.file_control.load_next_file())

        # check if finish session should be enabled
        idx = self.state.file_selected_idx.get()
        n_pdfs = len(self.state.pdf_collection.pdfs)
        if (idx + 1) == n_pdfs:
            self.file_control.btn_finish_session['state'] = 'normal'


    # switch between labels in bbox_label_dict
    def switch_label(self, direction):

        idx = self.state.page_bbox_label_idx.get()

        self.state.page_bbox_text_entry[idx]['lbl_widget'].config(background = 'white')

        if direction == 'next':
            if idx < len(self.state.pdf_collection.bbox_label_dict)-1:
                self.state.page_bbox_label_idx.set(idx + 1)
            else:
                self.state.page_bbox_label_idx.set(0)
        if direction == 'previous':
            if idx > 0:
                self.state.page_bbox_label_idx.set(idx - 1)
            else:
                self.state.page_bbox_label_idx.set(len(self.state.pdf_collection.bbox_label_dict)-1)

        self.state.page_bbox_text_entry[self.state.page_bbox_label_idx.get()]['lbl_widget'].config(background = 'red')

    def populate_ent_widgets(self):

        for k, v in self.state.page_bbox_text_entry.items():
            v['string_var'].set(self.state.page.labels.key_values[k])

        self._root().focus()

    def clear_ent_widgets(self):

        for k, v in self.state.page_bbox_text_entry.items():
            if k == 0:
                v['lbl_widget'].config(background = 'red')
            else:
                v['lbl_widget'].config(background = 'white')
            v['string_var'].set('')

    def extract_text(self, set_label = True):

        labeled_bboxes = [i for i in self.state.page.labels.tokens.values() if 'label' in i]

        self.label_bbox_id_dict = dict()
        for k in self.state.bbox_label_dict.keys():
            bbox_ids = [i['id'] for i in labeled_bboxes if i['label'] == k]
            self.label_bbox_id_dict[k] = bbox_ids

        print(self.label_bbox_id_dict)

        if set_label:
            self.state.page.labels.key_values = dict()
            for k, v in self.label_bbox_id_dict.items():
                joined_tokens = ' '.join([self.state.page.labels.tokens[i]['word'] for i in v])
                self.state.page.labels.key_values[k] = joined_tokens

        self.populate_ent_widgets()

    def check_values(self):

        print(self.hsn_df)
        print(self.tsn_df)

        if hasattr(self, 'label_bbox_id_dict'):
            if isinstance(self.state.page.labels.key_values, dict):
                for k, v in self.state.page_bbox_text_entry.items():
                    # if self.label_bbox_id_dict[k] != []:
                    self.state.page.labels.key_values[k] = v['string_var'].get()
                    print(v['string_var'].get())
                self.populate_ent_widgets()

        exit = []

        try:
            validate(self.state.page.labels.key_values[3])
        except:
            exit.append('Date')
        try:
            hsn = int(self.state.page.labels.key_values[4])
            self.hsn_intid = self.hsn_df.loc[hsn].intid
            self.lbl_hsn_value.config(text = self.hsn_df.loc[hsn].strname)
        except:
            exit.append('HSN')
        try:
            tsn = self.state.page.labels.key_values[5]
            tsn_row = self.tsn_df[self.tsn_df.strtsn == tsn[0:3]]
            tsn_row = tsn_row[tsn_row.intid_strhsn == self.hsn_intid]
            tsn_str = tsn_row.strname.values[0]
            self.tsn_intid = tsn_row.intid.values[0]
            self.intid_strwagnis = tsn_row.intid_strwagnis.values[0]
            self.lbl_tsn_value.config(text = tsn_str)
        except:
            exit.append('TSN')

        if exit != []:
            dialog = SimpleDialog(
                self._root(),
                text = f"Can't recognize {' '.join(exit)}",
                buttons=["Confirm"],
                default=0,
                cancel=1,
                title="Confirmation"
            )
            dialog.go()
        else:
            # write results to json
            import json
            with open('upload.json', 'wt') as file:
                json_result = self.state.page.labels.key_values
                idx = self.state.file_selected_idx.get()
                file_name, _ = self.state.indexed_files[idx]
                json_result['intid_strhersteller'] = self.hsn_intid
                json_result['intid_strtyp'] = self.tsn_intid
                json_result['intid_strwagnis'] = self.intid_strwagnis
                json_result['file_name'] = file_name
                print(json_result)
                json.dump(json_result, file)
            # activate save button
            self.btn_update_key_text['state'] = 'active'

    def update_key_text(self):

        dialog = SimpleDialog(
            self._root(),
            text="Please confirm your entry.",
            buttons=["Confirm", "Cancel"],
            default=0,
            cancel=1,
            title="Confirmation"
        )

        if dialog.go() == 0:

            self.state.page.labels.confirmed = True
            self.file_control.btn_next_file['state'] = 'normal'
            self._root().bind('x', lambda event: self.file_control.load_next_file())

            # check if btn_next_file should be enabled
            idx = self.state.file_selected_idx.get()
            n_pdfs = len(self.state.pdf_collection.pdfs)
            if (idx + 1) == n_pdfs:
                self.file_control.btn_finish_session['state'] = 'normal'
