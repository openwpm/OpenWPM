import json
import os

import jsonschema

curdir = os.path.dirname(os.path.realpath(__file__))


def get_default_log_settings():
    return {
        'propertiesToInstrument': [],
        'nonExistingPropertiesToInstrument': [],
        'excludedProperties': [],
        'logCallStack': False,
        'logFunctionsAsStrings': False,
        'logFunctionGets': False,
        'preventSets': False,
        'recursive': False,
        'depth': 5,
    }


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


def validate(python_list_to_validate):
    schema_path = os.path.join(
        curdir, 'js_instrumentation', 'js_instrument_modules.schema'
    )
    schema = json.loads(open(schema_path).read())
    jsonschema.validate(instance=python_list_to_validate, schema=schema)
    return True


def dedupe(python_list):
    return python_list


def get_instrumented_name(object):
    pass


def build_object_from_request(request):
    """
    We need to build a valid object from each request.

    The item may be a string or an object with one key.
    If the item is a string:
      - Is it a shortcut e.g. "fingerprinting"
      - Is it an object (verified by mdn-browser-compat)
      - If neither, reject
    If the item is an object:
      - Must only have one property
      - The value may be a list or a LogSettings object
      - If the value is a list, it is transformed into the
        propertiesToInstrument property of a new LogSettings object.
    We must also create the instrumentedName value.
    """
    return {}


def convert_browser_params_to_js_string(js_instrument_modules):
    """
    We accept a list. From the list we need to parse each item.
    Examples of the requests we accept.
    // Shortcut
    "fingerprinting",
    // APIs
    {"XMLHttpRequest": {"badSetting": 1}},
    {"XMLHttpRequest": {"excludedProperties": ["send"]}},
    {"Prop1": ["hi"], "Prop2": ["hi2"]},
    {"XMLHttpRequest": ["send"]},
    "Storage",
    // Specific instances on window
    {"window.document": ["cookie", "referrer"]},
    {"window": ["name", "localStorage", "sessionStorage"]}
    """
    assert isinstance(js_instrument_modules, list)
    requests = [
        build_object_from_request(request) for request in js_instrument_modules
    ]
    requests = dedupe(requests)
    validate(requests)
    return python_to_js_string(requests)
