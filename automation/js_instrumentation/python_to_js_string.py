import json


def python_to_js_string(py_in):
    """Takes python in and converts it to a string
    of the equivalent JS object.

    Customized for our specific needs:
    * expects a list
    * object is de-quoted
    """
    objects = [x['object'] for x in py_in]
    out = json.dumps(py_in)
    for o in objects:
        obj_str_before = f'"object": "{o}",'
        obj_str_after = f'"object": {o},'
        out = out.replace(obj_str_before, obj_str_after)
    return out
