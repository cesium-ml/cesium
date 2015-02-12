
def instantiate_nb(cells=False):
    nb = {
        "metadata": {
            "name": ""
        },
        "nbformat": 3,
        "nbformat_minor": 0,
        "worksheets": [
            {
                "cells": [],
                "metadata": {}
            }
        ]
    }
    
    if cells:
        nb = add_cells_to_nb(nb, cells)
    
    return nb





def create_code_cell(code_lines):
    lines_list = code_lines.split("\n")
    
    for i in range(len(lines_list)):
        if i < len(lines_list)-1:
            lines_list[i] += "\n"
    cell_dict = {
            "cell_type": "code",
            "collapsed": "false",
            "input": lines_list,
            "language": "python",
            "metadata": {},
            "outputs": []
        }
    
    return cell_dict





def add_cells_to_nb(nb, new_cell_contents):
    if type(new_cell_contents)==str:
        nb['worksheets'][0]['cells'].append(create_code_cell(new_cell_contents))
    elif type(new_cell_contents)==list and len(new_cell_contents) > 0:
        if type(new_cell_contents[0])==str:
            for new_cell in new_cell_contents:
                nb['worksheets'][0]['cells'].append(create_code_cell(new_cell))
        elif type(new_cell_contents[0])==dict:
            for new_cell in new_cell_contents:
                nb['worksheets'][0]['cells'].append(new_cell)
    elif type(new_cell_contents)==dict:
        nb['worksheets'][0]['cells'].append(new_cell_contents)
    
    return nb






def write_nb_to_file(nb, filename):
    if ".ipynb" not in filename:
        filename += ".ipynb"
    with open(filename,'w') as f:
        f.write(str(nb).replace("'",'"').replace('"false"',"false"))
    print(filename, "created.")
    return
