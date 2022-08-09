import tkinter as tk

# application state as class
class State:

    def __init__(self, master, pdf_collection, bbox_label_dict):

        # connect data source
        self.pdf_collection = pdf_collection
        if not hasattr(pdf_collection, 'overview'):
            self.pdf_collection.process_files()
        self.indexed_files = {i: (k, v) for i, (k, v) in enumerate(self.pdf_collection.pdfs.items())}

        # add label types
        self.bbox_label_dict = bbox_label_dict
        self.pdf_collection.bbox_label_dict = bbox_label_dict

        # define file-level states
        self.file_selected_idx = tk.IntVar(master)

        # define page-level states
        self.page = None
        self.page_edit_mode = tk.StringVar(master, value = 'preprocessing')
        self.page_bbox_label_idx = tk.IntVar(master)
        self.page_crop_bbox = None
        self.page_drawn_bbox = None
        self.page_token_bboxes = None
        self.page_bbox_text_entry = None

    def reset(self, pdf_collection, bbox_label_dict):

        # connect data source
        self.pdf_collection = pdf_collection
        if not hasattr(pdf_collection, 'overview'):
            self.pdf_collection.process_files()
        self.indexed_files = {i: (k, v) for i, (k, v) in enumerate(self.pdf_collection.pdfs.items())}

        # add label types
        self.bbox_label_dict = bbox_label_dict
        self.pdf_collection.bbox_label_dict = bbox_label_dict

        # define file-level states
        self.file_selected_idx.set(0)

        # define page-level states
        self.page_crop_bbox = None
        self.page_drawn_bbox = None
        self.page_token_bboxes = None


# class for page labels
class PageLabels:

    def __init__(self, rotation, crop_bbox, tokens, key_values):
        self.rotation = rotation
        self.crop_bbox = crop_bbox
        self.tokens = tokens
        self.key_values = key_values
