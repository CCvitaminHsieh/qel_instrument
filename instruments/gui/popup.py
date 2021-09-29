# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 23:35:09 2021

@author: QEL
"""

import tkinter as tk
from tkinter import filedialog


def popup_file_dialog(function_handle: str,
                      title: str,
                      filetype_description: str = 'JSON config',
                      filetype: str = '*.json'
                      ):
    """
    

    Parameters
    ----------
    function_handle : str
        DESCRIPTION.
    title : str
        DESCRIPTION.
    filetype_description : str
        DESCRIPTION.
    filetype : str, optional
        DESCRIPTION. The default is '*.json'.

    Returns
    -------
    fpath : TYPE
        DESCRIPTION.

    """
    root = tk.Tk()
    root.withdraw()
    if function_handle == 'w':
        fpath = filedialog.asksaveasfilename(
            parent=root,
            title=title,
            defaultextension=filetype,
            filetypes=[
                (filetype_description,
                 filetype)
            ]
        )
    elif function_handle == 'r':
        fpath = filedialog.askopenfilename(
            parent=root,
            title=title,
            defaultextension=filetype,
            filetypes=[
                (filetype_description,
                 filetype
                 )
            ]
        )
    
    return fpath