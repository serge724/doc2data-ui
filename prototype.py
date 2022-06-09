import os
from tkinter import *
from tkinter import ttk
import tkinter.font as tkf
from functions import *

# set up root window
root = Tk()

# adjust fonts
default_font = tkf.nametofont('TkDefaultFont')
text_font = tkf.nametofont('TkTextFont')
default_font.configure(size=16)
text_font.configure(size=16)
small_font = tkf.nametofont('TkTextFont')
small_font.configure(size=10)

# configure root window
root.title("Doc processing prototype")
root.columnconfigure(0, weight = 1, minsize=800)
root.columnconfigure(1, weight = 0, minsize=480)
root.rowconfigure(0, weight = 1, minsize=800)

# define main frames
frm_document = Frame(root, relief = GROOVE, borderwidth = 3)
frm_document.columnconfigure(0, weight = 1)
frm_document.rowconfigure(0, weight = 1)
frm_document.grid(row = 0, column = 0, sticky = 'ewns', padx = 2, pady = 2)
frm_controls = Frame(root, relief = GROOVE, borderwidth = 3)
frm_controls.grid(row = 0, column = 1, sticky = 'ewns', padx = 2, pady = 2)

# define control frames
frm_db_control = LabelFrame(frm_controls, relief = GROOVE, borderwidth = 3, text = 'Database')
frm_db_control.pack(fill = X, padx = 2, pady = 2)
frm_edit_control = LabelFrame(frm_controls, relief = GROOVE, borderwidth = 3, text = 'Edit')
frm_edit_control.pack(fill = X)
frm_mode_control = LabelFrame(frm_controls, relief = GROOVE, borderwidth = 3, text = 'Mode')
frm_mode_control.pack(fill = X)
frm_labeling_control = LabelFrame(frm_controls, relief = GROOVE, borderwidth = 3, text = 'Labeling')
frm_labeling_control.pack(fill = X)
frm_object_list = LabelFrame(frm_controls, relief = GROOVE, borderwidth = 3, text = 'Results')
frm_object_list.pack(fill = X)

# instantiate classes
doc = Document(frm_document)

# define database interface
btn_create_doc_db = Button(
    master = frm_db_control,
    text = 'Create database',
    command = doc.doc_db.create_db_dialogue,
    width = 20
)
btn_create_doc_db.pack()

btn_save_doc_db = Button(
    master = frm_db_control,
    text = 'Save database',
    command = doc.doc_db.save_db,
    width = 20
)
btn_save_doc_db.pack()

btn_load_doc_db = Button(
    master = frm_db_control,
    text = 'Load database',
    command = doc.doc_db.load_db_dialogue,
    width = 20
)
btn_load_doc_db.pack()

btn_load_previous = Button(
    master = frm_db_control,
    text = 'Load previous',
    command = lambda: doc.doc_db.push_document('previous'),
    width = 20
)
btn_load_previous.pack()

btn_load_next = Button(
    master = frm_db_control,
    text = 'Load next',
    command = lambda: doc.doc_db.push_document('next'),
    width = 20
)
btn_load_next.pack()

btn_reload = Button(
    master = frm_db_control,
    text = 'Reload',
    command = lambda: doc.doc_db.push_document('current'),
    width = 20
)
btn_reload.pack()

btn_rotate_left = Button(
    master = frm_edit_control,
    text = 'Rotate left',
    command = lambda: doc.rotate('left'),
    width = 20
)
btn_rotate_left.pack()

btn_rotate_right = Button(
    master = frm_edit_control,
    text = 'Rotate right',
    command = lambda: doc.rotate('right'),
    width = 20
)
btn_rotate_right.pack()

btn_binarize = Button(
    master = frm_edit_control,
    text = 'Binarize',
    command = doc.binarize,
    width = 20
)
btn_binarize.pack()

btn_binarize = Button(
    master = frm_edit_control,
    text = 'Crop',
    command = doc.crop,
    width = 20
)
btn_binarize.pack()

rbtn_crop_mode = Radiobutton(frm_mode_control, name = 'rbtn_crop_mode', text = 'Crop', variable = doc.processing_mode,
                            indicatoron = False, value = 'crop', width = 8, command = doc.update_canvas)
rbtn_crop_mode.pack(side = 'left')
rbtn_ocr_mode = Radiobutton(frm_mode_control, name = 'rbtn_ocr_mode', text = 'OCR', variable = doc.processing_mode,
                           indicatoron = False, value = 'ocr', width = 8, command = doc.update_canvas)
rbtn_ocr_mode.pack(side = 'left')
rbtn_labeling_mode = Radiobutton(frm_mode_control, name = 'rbtn_labeling_mode', text = 'Labeling', variable = doc.processing_mode,
                                indicatoron = False, value = 'labeling', width = 8, command = doc.update_canvas)
rbtn_labeling_mode.pack(side = 'left')

# allow doc object access to radio buttons
doc.mode_control_frame = frm_mode_control

btn_run_ocr = Button(
    master = frm_labeling_control,
    text = 'Run OCR',
    command = doc.run_full_ocr,
    width = 20
)
btn_run_ocr.pack()

btn_save_bbox = Button(
    master = frm_labeling_control,
    text = 'Save bounding box',
    command = lambda: doc.canvas.save_bbox(),
    width = 20
)
btn_save_bbox.pack()

btn_remove_last_bbox = Button(
    master = frm_labeling_control,
    text = 'Remove bounding box',
    command = lambda: doc.canvas.remove_last_bbox(),
    width = 20
)
btn_remove_last_bbox.pack()

btn_clean_labels = Button(
    master = frm_labeling_control,
    text = 'Clean labels',
    command = doc.clean_labels,
    width = 20
)
btn_clean_labels.pack()

# info on current document
lbl_file_info = Label(
    master = frm_object_list,
    textvariable = doc.file_info,
    font = small_font
)
lbl_file_info.pack()

# this is needed for treeview update
doc.label_keys = {
    0: 'Kennzeichen',
    1: 'Name',
    2: 'Vorname',
    3: 'Erstzulassung',
    4: 'Fahrzeugklasse',
    5: 'Handelsbez.',
    6: 'Herst.-Kurzbez.'
}

# ...
tree = ttk.Treeview(master = frm_object_list, columns = ['key', 'value'])
tree.column('#0', width = 5)
tree.column('key', width = 200)
tree.column('value', anchor = 'center', width = 200)
tree.heading('key', text = 'Schlüssel')
tree.heading('value', text = 'Wert')
tree.pack()

# allow doc object access to treeview widget
doc.treeview = tree

# ...
btn_save_doc = Button(
    master = frm_object_list,
    text = 'Save document',
    command = doc.doc_db.save_document,
    width = 20
)
btn_save_doc.pack()

# def temp_export():
#     doc.doc_db.save_document()
#     print(doc.doc_db.bbox_df)
#     for i, row in doc.doc_db.bbox_df.iterrows():
#         tree.insert('', END, values=(row['label'], row['text']))
#
# def temp_reload():
#     tree.delete(*tree.get_children())
#     doc.doc_db.push_document('current')
#
# def temp_load_next():
#     tree.delete(*tree.get_children())
#     doc.doc_db.push_document('next')

# btn_temp = Button(master = frm_object_list, text = 'Export results', command = temp_export)
# btn_temp.pack(side = 'left', padx = 10, pady = 10)

root.bind('c', lambda event: doc.crop())
root.bind('r', lambda event: doc.run_full_ocr())
root.bind('l', lambda event: doc.processing_mode.set('labeling'))
root.bind('o', lambda event: doc.processing_mode.set('ocr'))
root.bind('s', lambda event: doc.canvas.save_bbox())



# run app
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
root.mainloop()
