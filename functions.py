import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image, ImageTk
from skimage.filters import threshold_yen
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from tkinter import Canvas, Scrollbar, StringVar, IntVar
from tkinter.filedialog import askdirectory, askopenfilename, asksaveasfilename

# class for processing the selected document
class Document:

    def __init__(self, parent):

        self.doc_db = DocDatabase(self)
        self.canvas = DocCanvas(self, parent)
        self.tk_parent = parent
        self.label_keys = None
        self.selected_key = IntVar(value = 0)
        self.processing_mode = StringVar(value = 'crop')
        self.file_info = StringVar(value = 'No document loaded.')
        self.doc_dict = {} # all information from the current document is stored here

        self.mode_control_frame = None
        self.treeview = None

    def load_file(self):

        # self.canvas.__init__(self, self.t)
        # self.canvas = DocCanvas(self, self.tk_parent)
        path = os.path.join(self.doc_db.path_to_documents, self.doc_db.current_doc['file_name'])
        self.doc_dict = self.doc_db.current_doc.to_dict()
        self.original_image = convert_from_path(path)[0]
        self.processed_image = self.original_image
        self.displayed_image = self.original_image
        self.file_info.set('ID: %s \n File Name: %s'%(self.doc_db.current_idx, self.doc_db.current_doc['file_name']))

        # ...
        self.mode_control_frame.children['rbtn_crop_mode'].configure(state = 'active')
        self.canvas.delete('all')
        self.canvas.zoom = None
        self.canvas.b1_clicked = None
        self.canvas.drawn_bbox = None
        self.canvas.hovered_bbox = None
        self.canvas.crop_bbox = None
        self.canvas.bbox_list = []
        self.processing_mode.set('crop')
        self.refresh_treeview()
        self.update_canvas()

        if self.doc_dict['completed']:
            self.canvas.create_rectangle(100, 100, 300, 200, fill = 'red')

    def clean_labels(self):

        for bbox in self.canvas.bbox_list:
            if bbox.type == 'user':
                bbox.destroy()
            else:
                bbox.clicked = False
                bbox.label = None
                self.canvas.itemconfig(bbox.bbox_id, fill = 'red')

        self.refresh_treeview()
        self.update_canvas()

    def update_canvas(self):

        if self.processing_mode.get() == 'crop':
            self.canvas.delete('all')
            canvas_frame_width = self.tk_parent.winfo_width()
            canvas_frame_height = self.tk_parent.winfo_height()
            self.displayed_image = self.processed_image.copy()
            self.displayed_image.thumbnail((canvas_frame_width, canvas_frame_height))
            image = ImageTk.PhotoImage(self.displayed_image)
            self.canvas_img_id = self.canvas.create_image(0, 0, image = image, anchor = 'nw')
            self.canvas.image = image # due to bug (https://blog.furas.pl/python-tkinter-how-to-load-display-and-replace-image-on-label-button-or-canvas-gb.html)
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            self.canvas.zoom = self.displayed_image.size[0] / self.processed_image.size[0]
        else:
            image = ImageTk.PhotoImage(self.processed_image)
            self.canvas.itemconfig(self.canvas_img_id, image = image)
            self.canvas.image = image # due to bug (https://blog.furas.pl/python-tkinter-how-to-load-display-and-replace-image-on-label-button-or-canvas-gb.html)
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            self.canvas.zoom = 1

    def refresh_treeview(self):

        # refresh treeview
        self.selected_key.set(0)
        self.treeview.delete(*self.treeview.get_children())
        for i, key in self.label_keys.items():
            self.treeview.insert(parent = '', index = 'end', iid = i, values = (key, ''))
        self.treeview.focus(self.selected_key.get())
        self.treeview.selection_set(self.selected_key.get())

    def rotate(self, direction):

        if direction == 'left':
            self.processed_image = self.processed_image.rotate(angle = 90, expand = 1)
            self.doc_dict['rotation'] = self.doc_dict['rotation'] - 90

        if direction == 'right':
            self.processed_image = self.processed_image.rotate(angle = -90, expand = 1)
            self.doc_dict['rotation'] = self.doc_dict['rotation'] + 90

        self.update_canvas()

    def binarize(self):

        img_array = np.array(self.processed_image.convert(mode = 'L'))
        thresh = threshold_yen(img_array)
        self.binary_image = img_array > thresh
        self.processed_image = Image.fromarray(self.binary_image)
        self.processed_image = self.processed_image.convert(mode = 'RGB')
        self.is_binarized = True
        self.doc_dict['binarized'] = True

        self.update_canvas()

    def crop(self):
        if self.canvas.crop_bbox is not None:
            crop_bbox = self.canvas.crop_bbox
            coords = np.array([crop_bbox.start_x, crop_bbox.start_y, crop_bbox.end_x, crop_bbox.end_y])
            coords = np.round(coords / self.canvas.zoom)
            self.processed_image = self.processed_image.crop(coords)
            self.doc_dict['cropped_area'] = coords
            crop_bbox.destroy()

            self.mode_control_frame.children['rbtn_crop_mode'].configure(state = 'disabled')
            self.processing_mode.set('ocr')
            self.update_canvas()

    def run_full_ocr(self):

        self.ocr_result = run_paddle_ocr(self.processed_image)
        for i, row in self.ocr_result.iterrows():
            bbox = BoundingBox(self.canvas, 'ocr')
            bbox.draw_rectangle(row['bbox'])
            bbox.text = row['text']
            self.canvas.bbox_list.append(bbox)

        print('ocr processing successful')

class BoundingBox:

    def __init__(self, canvas, type):

        self.bbox_id = None
        self.canvas = canvas
        self.type = type
        self.label = None
        self.image_segment = None
        self.text = None
        self.clicked = False

    def draw_rectangle(self, bbox_coords):

        self.start_x, self.start_y, self.end_x, self.end_y = bbox_coords

        self.bbox_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            fill = 'red',
            stipple = 'gray25'
        )

    def add_start_corner(self, x, y):

        self.start_x = x
        self.start_y = y

    def drag_rectangle(self, x, y):

        self.end_x = x
        self.end_y = y

        if self.bbox_id is not None: self.canvas.delete(self.bbox_id)
        self.bbox_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            fill = 'yellow',
            stipple = 'gray25'
        )

    def run_ocr_on_segment(self):

        img = ImageTk.getimage(self.canvas.image)
        img = img.crop([self.start_x, self.start_y, self.end_x, self.end_y])
        self.image_segment = img.convert('RGB') # unintuitive behaviour of crop
        ocr_result = run_paddle_ocr(self.image_segment)
        self.text = ' '.join(ocr_result.text)

    def destroy(self):

        self.canvas.delete(self.bbox_id)

# ...
class CropBox(BoundingBox):

    pass


# canvas class with scrollbars for document visualisation
class DocCanvas(Canvas):

    def __init__(self, document, parent, **kwargs):

        super().__init__(parent, **kwargs)
        ## define and place canvas and scrollbars
        self.grid(row = 0, column = 0, sticky = 'ewns')
        sb_x = Scrollbar(parent, orient = 'horizontal', command = self.xview)
        sb_x.grid(row = 1, column = 0, sticky="ew")
        sb_y = Scrollbar(parent, orient = 'vertical', command = self.yview)
        sb_y.grid(row = 0, column = 1, sticky = 'ns')
        self.configure(yscrollcommand = sb_y.set, xscrollcommand = sb_x.set)

        # bind mouse events
        self.bind('<Motion>', self.on_motion)
        self.bind('<Button-1>', self.on_b1_click)
        self.bind('<B1-Motion>', self.on_b1_motion)
        self.bind('<ButtonRelease-1>', self.on_b1_release)

        self.document = document
        self.zoom = None
        self.b1_clicked = None
        self.drawn_bbox = None
        self.hovered_bbox = None
        self.crop_bbox = None
        self.bbox_list = []

    def on_motion(self, event):

        x = self.canvasx(event.x)
        y = self.canvasy(event.y)

        if len(self.bbox_list) > 0:
            if self.document.processing_mode.get() == 'ocr':

                ocr_bboxes = pd.DataFrame([i.__dict__ for i in self.bbox_list])
                ocr_bboxes['bbox_object'] = self.bbox_list
                ocr_bboxes = ocr_bboxes[ocr_bboxes.type == 'ocr']
                hover_bbox = ocr_bboxes[(ocr_bboxes.start_x < x) & (ocr_bboxes.end_x > x) &
                                        (ocr_bboxes.start_y < y) & (ocr_bboxes.end_y > y)]



                if hover_bbox.empty:
                    if self.hovered_bbox is not None:
                        # print(self.hovered_bbox.text)
                        if not self.hovered_bbox.clicked:
                            if self.hovered_bbox.label is None:
                                self.itemconfig(self.hovered_bbox.bbox_id, fill = 'red')
                                self.hovered_bbox = None
                else:
                    self.hovered_bbox = hover_bbox.iloc[0]['bbox_object']
                    # print(self.hovered_bbox.text)
                    if not self.hovered_bbox.clicked:
                        if self.hovered_bbox.label is None:
                            self.itemconfig(self.hovered_bbox.bbox_id, fill = 'magenta')

    def on_b1_click(self, event):

        x = self.canvasx(event.x)
        y = self.canvasy(event.y)

        if self.document.processing_mode.get() == 'labeling':
            if self.drawn_bbox is not None: self.drawn_bbox.destroy()
            self.drawn_bbox = BoundingBox(self, 'user')
            self.drawn_bbox.add_start_corner(x, y)

        if self.document.processing_mode.get() == 'ocr':
            if self.hovered_bbox is not None:
                if not self.hovered_bbox.clicked:
                    if self.hovered_bbox.label is None:
                        self.hovered_bbox.clicked = True
                        self.itemconfig(self.hovered_bbox.bbox_id, fill = 'yellow')
                else:
                    self.hovered_bbox.clicked = False
                    self.itemconfig(self.hovered_bbox.bbox_id, fill = 'red')

        if self.document.processing_mode.get() == 'crop':
            if self.crop_bbox is not None: self.crop_bbox.destroy()
            self.crop_bbox = CropBox(self, 'crop_box')
            self.crop_bbox.add_start_corner(x, y)

    def on_b1_motion(self, event):

        x = self.canvasx(event.x)
        y = self.canvasy(event.y)

        if self.document.processing_mode.get() == 'labeling':
            self.drawn_bbox.drag_rectangle(x, y)

        if self.document.processing_mode.get() == 'crop':
            self.crop_bbox.drag_rectangle(x, y)

    def on_b1_release(self, event):

        if self.document.processing_mode.get() == 'labeling':
            # check, if bbox was drawn or if there was only a click
            if hasattr(self.drawn_bbox, 'end_x'):
                # adjust coordinates if box was drawn not from top left to bottom right
                if self.drawn_bbox.start_x > self.drawn_bbox.end_x:
                    self.drawn_bbox.start_x, self.drawn_bbox.end_x = self.drawn_bbox.end_x, self.drawn_bbox.start_x
                if self.drawn_bbox.start_y > self.drawn_bbox.end_y:
                     self.drawn_bbox.start_y, self.drawn_bbox.end_y = self.drawn_bbox.end_y, self.drawn_bbox.start_y

                self.drawn_bbox.run_ocr_on_segment()
            else:
                self.drawn_bbox.destroy()

        if self.document.processing_mode.get() == 'crop':
            # check, if bbox was drawn or if there was only a click
            if hasattr(self.crop_bbox, 'end_x'):
                # adjust coordinates if box was drawn not from top left to bottom right
                if self.crop_bbox.start_x > self.crop_bbox.end_x:
                    self.crop_bbox.start_x, self.crop_bbox.end_x = self.crop_bbox.end_x, self.crop_bbox.start_x
                if self.crop_bbox.start_y > self.crop_bbox.end_y:
                     self.crop_bbox.start_y, self.crop_bbox.end_y = self.crop_bbox.end_y, self.crop_bbox.start_y

            else:
                self.crop_bbox.destroy()

    def save_bbox(self, *args):

        if self.document.processing_mode.get() == 'labeling':
            if self.drawn_bbox is not None:
                self.itemconfig(self.drawn_bbox.bbox_id, fill = 'lime green')
                self.drawn_bbox.label = self.document.label_keys[self.document.selected_key.get()]
                selection_text = self.drawn_bbox.text
                self.bbox_list.append(self.drawn_bbox)
                self.drawn_bbox = None
                print('labeled bounding box saved')

        if self.document.processing_mode.get() == 'ocr':

            # extract information from selected bounding boxes
            selection_text = []
            for box in self.bbox_list:
                if box.clicked:
                    box.clicked = False
                    box.label = self.document.label_keys[self.document.selected_key.get()]
                    self.itemconfig(box.bbox_id, fill = 'green')
                    selection_text.append(box.text)
            selection_text = ' '.join(selection_text)
            print('OCR selection saved')

        # update treeview
        tree = self.document.treeview
        tree.item(
            tree.focus(),
            values = [self.document.label_keys[self.document.selected_key.get()], selection_text]
        )

        # move to next key
        self.document.selected_key.set((self.document.selected_key.get() + 1))
        if self.document.selected_key.get() == len(self.document.label_keys):
            self.document.selected_key.set(0)
        self.document.treeview.focus(self.document.selected_key.get())
        self.document.treeview.selection_set(self.document.selected_key.get())

    def remove_last_bbox(self):

        last_bbox = self.bbox_list[-1]
        if last_bbox.type == 'user':
            last_bbox.destroy()
            self.bbox_list.remove(last_bbox)
            self.document.selected_key.set((self.document.selected_key.get() - 1))
            self.document.treeview.focus(self.document.selected_key.get())
            self.document.treeview.selection_set(self.document.selected_key.get())


# class to access documents
class DocDatabase:

    def __init__(self, document):

        self.document = document
        self.loaded = False

    def create_db(self, path_to_documents):

        file_names = os.listdir(path_to_documents)
        self.path_to_documents = path_to_documents
        self.n_docs = len(file_names)

        doc_dict = {}

        for i, j in enumerate(file_names):
            doc_dict[i] = {
                'type': 'kfz_schein',
                'file_name': j,
                'image_size': None,
                'binarized': False,
                'rotation': 0,
                'cropped_area': None,
                'objects': [],
                'completed': False
            }

        self.doc_df = pd.DataFrame(doc_dict).transpose()

        if all(self.doc_df.completed):
            self.current_idx = 0
        else:
            self.current_idx = np.where(self.doc_df.completed == False)[0][0]

        self.loaded = True
        print('database created')
        self.push_document('current')

    def push_document(self, type):

        if type == 'current':
            self.current_doc = self.doc_df.iloc[self.current_idx].copy()
            self.document.load_file()
        elif type == 'next':
            self.current_idx += 1
            self.current_doc = self.doc_df.iloc[self.current_idx].copy()
            self.document.load_file()
        elif type == 'previous':
            if self.current_idx > 0: self.current_idx -= 1
            self.current_doc = self.doc_df.iloc[self.current_idx].copy()
            self.document.load_file()

    def create_db_dialogue(self):
        # self.create_db(askdirectory())
        self.create_db('/home/sergej/projects/arcd/doc_processing_prototype/kfz-scheine')

    def save_db(self):

        if self.loaded:
            dir_name = 'databases'
            os.makedirs(dir_name, exist_ok = True)

            path_to_db = asksaveasfilename()
            dict_to_save = self.__dict__.copy()
            dict_to_save.pop('document')

            with open(path_to_db, 'wb') as file:
                pickle.dump(dict_to_save, file)

            # save extra copy
            os.makedirs('safety_db', exist_ok = True)
            date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
            db_name = 'safety_db/%s_doc_db.pickle'%date
            with open(db_name, 'wb') as file:
                pickle.dump(dict_to_save, file)

            print('db saved')

        else:
            print('database not created')

    def load_db(self, path_to_db):

        with open(path_to_db, 'rb') as file:
            loaded_dict = pickle.load(file)
            for i, j in loaded_dict.items():
                self.__setattr__(i, j)

    def load_db_dialogue(self):

        path_to_db = askopenfilename()
        if isinstance(path_to_db, str):
            self.load_db(path_to_db)
            self.current_idx = self.doc_df.completed[self.doc_df.completed == False].index[0]
            self.push_document('current')
        else:
            print('db loading failed')

    def save_document(self):

        if not self.document.doc_dict['completed']:

            os.makedirs('temp', exist_ok = True)
            # mark document as completed
            self.document.doc_dict['completed'] = True

            # add bounding boxes to document dictionary
            bboxes = [i.__dict__.copy() for i in self.document.canvas.bbox_list]
            [i.pop('canvas') for i in bboxes]
            [i.pop('image_segment') for i in bboxes]
            [i.pop('clicked') for i in bboxes]
            self.document.doc_dict['objects'] = bboxes

            # update correct row in document dataframe
            self.current_doc = pd.Series(self.document.doc_dict)
            self.doc_df.iloc[self.current_idx] = self.current_doc

            self.push_document('next')

            print('changes saved')

        else:
            print('document already completed')



def run_paddle_ocr(img):
    ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
    ocr_data = ocr_engine.ocr(np.array(img))
    ocr_data = pd.DataFrame({
        'token_id': list(range(len(ocr_data))),
        'text': [line[1][0] for line in ocr_data],
        'score': [line[1][1] for line in ocr_data],
        'precise_bbox': [line[0] for line in ocr_data]
    })
    aligned_bboxes = []
    for box in ocr_data.precise_bbox:
        x1 = np.min([i[0] for i in box])
        y1 = np.min([i[1] for i in box])
        x2 = np.max([i[0] for i in box])
        y2 = np.max([i[1] for i in box])
        aligned_bboxes.append((x1, y1, x2, y2))
    ocr_data['bbox'] = aligned_bboxes

    return ocr_data


# ...
if False:
    from tkinter import *
    root = Tk()
    frm_document = Frame(root, relief = GROOVE, borderwidth = 3)
    frm_document.columnconfigure(0, weight = 1)
    frm_document.rowconfigure(0, weight = 1)
    frm_document.grid(row = 0, column = 0, sticky = 'ewns', padx = 2, pady = 2)
    frm_controls = Frame(root, relief = GROOVE, borderwidth = 3)
    frm_controls.grid(row = 0, column = 1, sticky = 'ewns', padx = 2, pady = 2)

    self = Document(root)
    self.tk_parent.children['!frame'].winfo_width()
    self.doc_db.create_db_dialogue()
    self.doc_db.push_document('current')
    self.rotate('left')
    # from PIL import Image
    # img = Image.open('image.png')
    # run_paddle_ocr(img)

    temp = run_paddle_ocr(self.processed_image)
    temp

    self.run_full_ocr()
    t = self.canvas.bbox_list[0]

    temp = [i.__dict__ for i in self.canvas.bbox_list]
    for i in temp:
        i.pop('canvas')
        i.pop('image_segment')

    ' '.join(pd.DataFrame(temp)[0:2].text)

    pd.DataFrame(temp).to_csv('selection.csv')

    self.doc_db.load_db_dialogue()
    root.destroy()





    t = run_paddle_ocr(Image.open('temp/11-595387-1511001298-2015090311020300.tiff'))
    for i, row in t.iterrows():
        row['bbox']


    with open('temp.pickle', 'rb') as file:
        dat = pickle.load(file)

    t = pd.DataFrame(dat)
    t = t[t.type == 'ocr']
    t['label'] = pd.nan
    t.label == None
    point = (1145, 50)
    t
    t[(t.start_x < point[0]) & (t.end_x > point[0]) & (t.start_y < point[1]) & (t.end_y > point[1])]


    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    img = convert_from_path('kfz-scheine/11-018599-1711000464-2017040120491800.pdf')[0]
    ocr_data = ocr.ocr(np.array(img))
