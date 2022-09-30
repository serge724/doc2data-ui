import tkinter as tk
from doc2data.pdf import PDFCollection
from components.state import State
from components.controls import FileControl, PageControl, PageLevelProcessing

import sv_ttk

# define main app class
class App:

    def __init__(self, pdf_collection, config):

        # process config
        bbox_label_dict = config['bbox_labels']
        if config['only_values']:
            for k in list(bbox_label_dict.keys()):
                bbox_label_dict[int(k)] = bbox_label_dict.pop(k)
        else:
            shift = 0
            for k in list(bbox_label_dict.keys()):
                v = bbox_label_dict.pop(k)
                bbox_label_dict[int(k)+shift] = v + '_key'
                bbox_label_dict[int(k)+shift+1] = v + '_value'
                shift += 1

        # set up window
        self.root = tk.Tk()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+3440+0"%(1920, 1080))
        sv_ttk.set_theme("light")

        # initiate internal state
        self.state = State(self.root, pdf_collection, bbox_label_dict)

        # define UI elements
        file_control = FileControl(self.root, self.state, relief = 'groove', borderwidth = 3)
        page_processing = PageLevelProcessing(self.root, self.state, config['only_values'])

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


# start application
if __name__ == '__main__':

    import os
    import argparse
    import tomli

    # parse config file
    parser = argparse.ArgumentParser(description = 'Select configuration TOML.')
    parser.add_argument('--config', help = 'path of the TOML configuration file', default = 'config.toml')
    args = parser.parse_args()
    with open(args.config, 'rb') as file:
        config = tomli.load(file)

    # create collection from example files if started for the first time
    if os.path.exists('tmp/last_collection.pickle'):
        pdf_collection = PDFCollection.load('tmp/last_collection.pickle')
    else:
        pdf_collection = PDFCollection('example_docs/')

    app = App(pdf_collection, config)
    app.run()
