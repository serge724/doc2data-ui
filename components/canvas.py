import tkinter as tk
import tkinter.ttk as ttk
from doc2data.utils import normalize_bbox, denormalize_bbox
from tkinter.font import Font
from PIL import ImageTk

# ...
class BoundingBox:

    def __init__(self, master_canvas, type, token_id = None):

        self.canvas = master_canvas
        self.type = type

        # token_id from dict in labels has to be linked
        self.token_id = token_id
        if self.type == 'ocr_token':
            assert(token_id is not None), 'Token id missing in BoundingBox initialization.'

        self.rectangle_id = None
        self.label = None
        self.image_width = self.canvas.tk_image.width()
        self.image_height = self.canvas.tk_image.height()
        self.font = Font(size = 15, weight = 'bold')

    def add_start_corner(self, x, y):

        self.start_x = x
        self.start_y = y

    def drag_rectangle(self, x, y):

        self.end_x = x
        self.end_y = y

        if self.rectangle_id is not None: self.canvas.delete(self.rectangle_id)
        self.rectangle_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            fill = 'yellow',
            stipple = 'gray12'
        )

    def draw_rectangle(self, bbox_coords, activefill = None):

        self.start_x, self.start_y, self.end_x, self.end_y = bbox_coords

        self.rectangle_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            fill = 'red',
            activefill = 'magenta',
            stipple = 'gray12'
        )

    def on_click(self):

        if self.canvas.state.page_edit_mode.get() == 'ocr':
            if self.type == 'ocr_token':
                if self.label is None:
                    self.set_label(self.canvas.state.page_bbox_label_idx.get())
                else:
                    self.remove_label()
            if self.type == 'user':
                print(self.token_id)
                self.remove_label()
                print(self.label)
                self.canvas.state.page.labels.tokens.pop(self.token_id)
                print(self.canvas.state.page.labels.tokens)
                self.destroy()

        if self.canvas.state.page_edit_mode.get() == 'drawing':
            if self.type == 'user':
                if self.label is None:
                    self.set_label(self.canvas.state.page_bbox_label_idx.get())
                    self.canvas.state.page_drawn_bbox = None
                else:
                    self.remove_label()
                    self.canvas.state.page.labels.tokens.pop(self.token_id)
                    self.destroy()

    def set_label(self, label):
        # add label to bboxes
        self.label = label
        # add label to database
        self.canvas.state.page.labels.tokens[self.token_id]['label'] = label
        # adjust bounding box appearence
        if self.type == 'ocr_token':
            self.canvas.itemconfig(self.rectangle_id, fill = 'green', activefill = 'lime')
        if self.type == 'user':
            self.canvas.itemconfig(self.rectangle_id, fill = 'mediumblue', activefill = 'deepskyblue')

        self.text_id = self.canvas.create_text(self.end_x+2, self.start_y+2, text = label, anchor = 'nw', fill = 'red', font = self.font)

    def remove_label(self):
        # add label to bboxes
        self.label = None
        # add label to database
        self.canvas.state.page.labels.tokens[self.token_id]['label'] = None
        # adjust bounding box appearence
        self.canvas.itemconfig(self.rectangle_id, fill = 'red', activefill = 'magenta')
        self.canvas.delete(self.text_id)

    def align_coords(self):
        # align coordinates if box was drawn not from top left to bottom right
        if self.start_x > self.end_x:
            self.start_x, self.end_x = self.end_x, self.start_x
        if self.start_y > self.end_y:
             self.start_y, self.end_y = self.end_y, self.start_y

    def get_normalized_coords(self):

        return normalize_bbox([self.start_x, self.start_y, self.end_x, self.end_y], self.image_width, self.image_height)

    def get_image_segment(self):

        image = ImageTk.getimage(self.canvas.tk_image)
        image = image.convert('RGB') # ImageTk return RGBA mode
        segment = image.crop([self.start_x, self.start_y, self.end_x, self.end_y])

        return segment

    def destroy(self):
        print('destroy')
        print(self.rectangle_id)

        self.canvas.delete(self.rectangle_id)
        del self # TODO: check if necessary

# class for plain canvas with scrollbars in a frame
class ScrollableCanvas(tk.Canvas):

    def __init__(self, master, *args, **kwargs):

        # create & configure form that contains canvas & scrollbars
        self.frm_container = ttk.Frame(master = master)
        self.frm_container.columnconfigure(0, weight = 1)
        self.frm_container.rowconfigure(0, weight = 1)

        # initialize and place canvas on form container
        super().__init__(master = self.frm_container, **kwargs)
        self.grid(row = 0, column = 0)
        # place & configure scrollbars
        sb_x = ttk.Scrollbar(master = self.frm_container, orient = 'horizontal', command = self.xview)
        sb_x.grid(row = 1, column = 0, sticky= 'ew')
        sb_y = ttk.Scrollbar(master = self.frm_container, orient = 'vertical', command = self.yview)
        sb_y.grid(row = 0, column = 1, sticky = 'ns')
        self.configure(yscrollcommand = sb_y.set, xscrollcommand = sb_x.set)

# ...
class PageCanvas(ScrollableCanvas):

    def __init__(self, master, state, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.state = state

        # bind mouse events
        self.bind('<Button-1>', self.on_b1_click)
        self.bind('<B1-Motion>', self.on_b1_motion)
        self.bind('<ButtonRelease-1>', self.on_b1_release)

        # ...
        self.bind('<Motion>', self.on_motion)

        self.bind('<Double-Button-1>', lambda event: self.adjust_size())
        self.bind("<MouseWheel>", lambda event: self.yview_scroll(-event.delta//120, "units"))

    # override tk.Canvas method with custom image creation
    def create_image(self, image):
        tk_image = ImageTk.PhotoImage(image)
        self.canvas_img_id = super().create_image(0, 0, image=tk_image, anchor='nw')
        self.tk_image = tk_image # due to bug (https://blog.furas.pl/python-tkinter-how-to-load-display-and-replace-image-on-label-button-or-canvas-gb.html)
        self.adjust_size()
        self.configure(scrollregion=self.bbox('all'))

    def adjust_size(self):
        self.master.update()
        self.configure(
            width = min(self.tk_image.width(), self.master.winfo_width()-30),
            height = min(self.tk_image.height(), self.master.winfo_height())
        )

    def on_motion(self, event):
        pass
        #print(event.x, event.y)

    def on_b1_click(self, event):

        self.clicked_x = self.canvasx(event.x)
        self.clicked_y = self.canvasy(event.y)

        if self.state.page_edit_mode.get() == 'preprocessing':
            if self.state.page_crop_bbox is not None:
                self.state.page_crop_bbox.destroy()
                self.state.page_crop_bbox = None

        if self.state.page_edit_mode.get() == 'drawing':
            if self.state.page_drawn_bbox is not None:
                self.state.page_drawn_bbox.destroy()
                self.state.page_drawn_bbox = None

    def on_b1_motion(self, event):

        if self.state.page_edit_mode.get() == 'preprocessing':
            if self.state.page_crop_bbox is None:
                self.state.page_crop_bbox = BoundingBox(self, 'crop_bbox')
                self.state.page_crop_bbox.add_start_corner(self.clicked_x, self.clicked_y)

        if self.state.page_edit_mode.get() == 'drawing':
            if self.state.page_drawn_bbox is None:
                self.state.page_drawn_bbox = BoundingBox(self, 'user')
                self.state.page_drawn_bbox.add_start_corner(self.clicked_x, self.clicked_y)

        x = self.canvasx(event.x)
        y = self.canvasy(event.y)

        if self.state.page_edit_mode.get() == 'preprocessing':
            self.state.page_crop_bbox.drag_rectangle(x, y)

        if self.state.page_edit_mode.get() == 'drawing':
            self.state.page_drawn_bbox.drag_rectangle(x, y)

    def on_b1_release(self, event):

        self.clicked_x = None
        self.clicked_y = None

        if self.state.page_edit_mode.get() == 'preprocessing':
            if self.state.page_crop_bbox is not None:
                bbox = self.state.page_crop_bbox
                # check, if bbox was drawn or if there was only a click
                bbox.align_coords()
                bbox.normalized_coords = bbox.get_normalized_coords()

        if self.state.page_edit_mode.get() == 'drawing':
            if self.state.page_drawn_bbox is not None:
                bbox = self.state.page_drawn_bbox
                # check, if bbox was drawn or if there was only a click
                bbox.align_coords()
                bbox.normalized_coords = bbox.get_normalized_coords()


    def set_crop_box(self, bbox_coords):

        self.state.page_crop_bbox = BoundingBox(self, 'crop_bbox')
        self.state.page_crop_bbox.draw_rectangle(bbox_coords)
