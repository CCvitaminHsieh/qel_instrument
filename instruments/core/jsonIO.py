import json
from copy import deepcopy


def configIO(template_file_name: str,
             function_handle: str,
             export_configs: dict = None):
    """
    Import the existing config (*.json), and return its config.
    Export the existing config (properties) to JSON file.
    
    Parameters
    ----------
    template_file_name : str
        JSON file name.
    function_handle : str
        1. 'w': write mode.
            Export
        2. 'r': read mode.
            Import
    export_configs : dict, optional
        properties. The default is None.

    Returns
    -------
    result : TYPE
        DESCRIPTION.

    """
    if function_handle == 'w':
        if export_configs is not None:
            with open(template_file_name, 'w', encoding='utf-8') as obj:
                json.dump(export_configs, obj, indent=4, sort_keys=False)
                result =\
                    f'Generate this config to the following path\n' +\
                    f'{template_file_name}'
        else:
            result = 'Please give me a configuration to export.'
        print(result)
    elif function_handle == 'r':
        print('Import recipt.')
        with open(template_file_name, 'r') as obj:
            result = json.load(obj)
        return result

def jsonFormat(importJsonCfg: dict = None,
               indent: int = 4,
               sort: bool = False):
    """
    JSON print beautifully.
    
    Parameters
    ----------
    importJsonCfg : dict, optional
        Configuration. The default is None.
    indent : int, optional
        Indent. The default is 4.
    sort : bool, optional
        Configuration Sorting. The default is False.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    if importJsonCfg is not None:
        format_layout = json.dumps(
            importJsonCfg,
            indent=indent,
            separators=(',', ': '),
            sort_keys=sort)
        return format_layout
    else:
        return 'Nothing here in importJsonFile.'
