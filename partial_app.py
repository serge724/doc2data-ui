import tkinter as tk
import tkinter.ttk as ttk
from doc2data.pdf import PDFCollection
from canvas import PageCanvas, BoundingBox
from components import FileControl, PageControl
from state import State, PageLabels

from datetime import datetime
from doc2data.utils import denormalize_bbox
from doctr_ocr import run_doctr_ocr
from PIL import Image, ImageDraw


# define main app class
class App:

    def __init__(self, bbox_label_dict):

        # set up window
        self.root = tk.Tk()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+3440+0"%(1920, 1080))

        # initiate internal state
        pdf_collection = PDFCollection.load('db/pdf_collection.pickle')
        self.state = State(self.root, pdf_collection, bbox_label_dict)

        # define UI elements
        file_control = FileControl(self.root, self.state, relief = 'groove', borderwidth = 3)
        page_processing = PageLevelProcessing(self.root, self.state, style = 'lightgreen_frame.TFrame')

        # place UI elements
        page_processing.canvas.frm_container.pack(side = 'left', anchor = 'n', fill = 'both', expand = True, padx = 10, pady = 10)
        file_control.pack(side = 'top', padx = 10, pady = 10, fill = 'both')
        page_processing.control.pack(side = 'top', padx = 10, pady = 10, fill = 'both')
        page_processing.bbox_label_control.pack(side = 'top', padx = 10, pady = 10, fill = 'both')

    def run(self):
        # initiate first document
        if hasattr(self.state.pdf_collection, 'file_selected_idx'):
            idx = self.state.pdf_collection.file_selected_idx
        else:
            idx = 0
        self.root.after(1000, lambda: self.state.file_selected_idx.set(idx))
        self.root.mainloop()

class BboxLabelControl(ttk.LabelFrame):

    def __init__(self, master, state, page_analysis, *args, **kwargs):
        super().__init__(master, text = 'Labeling', *args, **kwargs)

        # attach state and link parent component
        self.state = state
        self.page_analysis = page_analysis

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
        self.state.page_bbox_text_entry = {}
        for k, v in self.state.pdf_collection.bbox_label_dict.items():
            lbl_label_key = ttk.Label(frm_bbox_labeling, text = '%s: %s'%(k, v))
            lbl_label_key.grid(column = 0, row = k, sticky = 'w')
            bbox_text = tk.StringVar()
            # ent_bbox_text = ttk.Entry(frm_bbox_labeling, textvariable = bbox_text, font = 'default 16').grid(column = 1, row = k, sticky = 'w')
            ent_bbox_text = ttk.Entry(frm_bbox_labeling, textvariable = bbox_text).grid(column = 1, row = k, sticky = 'w')
            self.state.page_bbox_text_entry[k] = {'lbl_widget': lbl_label_key, 'string_var': bbox_text}
        frm_bbox_labeling.pack(side = 'top', pady = 20)

        btn_update_key_text = ttk.Button(
            master = self,
            text = 'Update value text',
            command = self.update_key_text
        )
        btn_update_key_text.pack(side = 'top', padx = 2, pady = 2)

        # temp
        self._root().bind('e', lambda event: self.extract_text())

    # switch between labels in bbox_label_dict
    def switch_label(self, direction):

        idx = self.state.page_bbox_label_idx.get()

        self.state.page_bbox_text_entry[idx]['lbl_widget'].config(background = '')
        print(self.state.page_bbox_text_entry[idx]['lbl_widget'].cget('background'))

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

        self.state.page_bbox_text_entry[self.state.page_bbox_label_idx.get()]['lbl_widget'].config(background = 'white')

    def populate_ent_widgets(self):

        for k, v in self.state.page_bbox_text_entry.items():
            v['string_var'].set(self.state.page.labels.key_values[k])
            print(v['string_var'].get())

        self._root().focus()

    def clear_ent_widgets(self):

        for k, v in self.state.page_bbox_text_entry.items():
            v['lbl_widget'].config(background = '')
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
                print(joined_tokens)

        self.populate_ent_widgets()

    def update_key_text(self):

        if hasattr(self, 'label_bbox_id_dict'):
            for k, v in self.state.page_bbox_text_entry.items():
                if self.label_bbox_id_dict[k] != []:
                    self.state.page.labels.key_values[k] = v['string_var'].get()
            self.populate_ent_widgets()


# ...
class PageLevelProcessing(ttk.Frame):

    def __init__(self, master, state, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # attach state and callbacks
        self.state = state
        self.state.file_selected_idx.trace_add('write', self.on_file_change)
        self.state.page_edit_mode.trace_add('write', self.on_mode_change)

        # define ui components
        self.canvas = PageCanvas(master, state, bg = 'gray')
        self.control = PageControl(master, state, self, relief = 'groove', borderwidth = 3)
        self.bbox_label_control = BboxLabelControl(master, state, self, relief = 'groove', borderwidth = 3)

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
            self.state.page.labels = PageLabels(0, None, None, None)
        self.processed_image = self.state.page.read_content('image', dpi = 100, force_rgb = True)
        self.state.page_is_cropped = False
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
        self.state.pdf_collection.save('db/pdf_collection.pickle', overwrite = True)

        # select new file and page
        file_name, file = self.state.indexed_files[self.state.file_selected_idx.get()]
        self.state.page = file.processed_pages[0]

        # reset bbox_label_control
        self.bbox_label_control.clear_ent_widgets()

        # set state of the app according to available labels
        self.state.page_edit_mode.set('preprocessing')
        self.state.page_bbox_label_idx.set(0)
        if self.state.page.labels.crop_bbox is not None:
            self.after(900, lambda: self.state.page_edit_mode.set('ocr'))

    # callback that handels change of edit mode
    def on_mode_change(self, *args):

        # preprocessing mode
        if self.state.page_edit_mode.get() == 'preprocessing':

            print('preprocessing mode')
            self.load_page()

            # rotate if rotation label exists
            if self.state.page.labels.rotation != 0:
                self.after(300, lambda: self.rotate(self.state.page.labels.rotation, set_label = False))
            # draw crop bbox if label exists
            if self.state.page.labels.crop_bbox is not None:
                self.after(600, lambda: self.define_crop_bbox(set_label = False))

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
                if w < 500 or h < 500:
                    canvas_frame_width = self.canvas.winfo_width()
                    canvas_frame_height = self.canvas.winfo_height()
                    zoom = min((canvas_frame_width / w, canvas_frame_height / h))
                    self.processed_image = self.processed_image.resize((int(w*zoom), int(h*zoom)))
                # update state
                self.state.page_is_cropped = True
                crop_bbox.destroy()
                self.update_canvas()

            # load tokens if ocr labels exist
            if self.state.page.labels.tokens is not None:
                self.after(300, lambda: self.run_ocr(set_label = False))

            if self.state.page.labels.key_values is not None:
                self.after(600, lambda: self.bbox_label_control.extract_text(set_label = False))

        # bbox drawing mode
        elif self.state.page_edit_mode.get() == 'drawing':
            print('drawing mode')

    # resets all page labels
    def reset(self):
        file_name, file = self.state.indexed_files[self.state.file_selected_idx.get()]
        self.state.page = file.processed_pages[0]
        self.state.page.labels = PageLabels(0, None, None, None)
        self.state.page_edit_mode.set('preprocessing')

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

# start application
if __name__ == '__main__':

    bbox_label_dict = {
        0: 'Kennzeichen',
        1: 'Name',
        2: 'Vorname',
        3: 'Erstzulassung',
        4: 'Fahrzeugklasse',
        5: 'Handelsbez.',
        6: 'Herst.-Kurzbez.'
    }

    app = App(bbox_label_dict)
    app.run()
