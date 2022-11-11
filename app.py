import tkinter as tk
import tkinter.font as tkf
from doc2data.pdf import PDFCollection
from components.state import State
from components.controls import FileControl, PageControl, PageLevelProcessing


# define main app class
class App:

    def __init__(self, pdf_collection, config):

        # set up window
        self.root = tk.Tk()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+3440+0"%(1920, 1080))

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
        if config['sv_theme']:
            import sv_ttk
            sv_ttk.set_theme("light")
        if config['font_size'] != 'default':
            default_font = tkf.nametofont('TkDefaultFont')
            default_font.configure(size = config['font_size'])
            # text_font = tkf.nametofont('TkTextFont')
            # text_font.configure(size=16)


        # initiate internal state
        self.state = State(self.root, pdf_collection, bbox_label_dict)

        # define UI elements
        file_control = FileControl(self.root, self.state, relief = 'groove', borderwidth = 3)
        page_processing = PageLevelProcessing(
            self.root,
            self.state,
            file_control,
            config['only_values'],
            config['hsn_df'],
            config['tsn_df']
        )

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
    ## load HSN values
    import pandas as pd
    config['hsn_df'] = pd.read_csv('hsn.csv').set_index('strhsn')
    config['tsn_df'] = pd.read_csv('tsn.csv').set_index('strtsn')

    # create collection from example files if started for the first time
    if os.path.exists('tmp/last_collection.pickle'):
        pdf_collection = PDFCollection.load('tmp/last_collection.pickle')
    else:
        pdf_collection = PDFCollection(config['default_folder'])

    app = App(pdf_collection, config)
    app.run()
