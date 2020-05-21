import json
import os
import jsonschema
from .js_instrumentation.mdn_browser_compat_data import api as mdn


curdir = os.path.dirname(os.path.realpath(__file__))
schema_path = os.path.join(
    curdir, 'js_instrumentation', 'js_instrument_modules.schema'
)

list_log_settings = [
    'propertiesToInstrument',
    'nonExistingPropertiesToInstrument',
    'excludedProperties'
]
shortcut_specs = {
    'fingerprinting': os.path.join(curdir, 'js_instrumentation', 'fingerprinting.json')
}


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
    schema = json.loads(open(schema_path).read())
    jsonschema.validate(instance=python_list_to_validate, schema=schema)
    # Check properties to instrument and excluded properties don't collide
    for request in python_list_to_validate:
        propertiesToInstrument = set(
            request['logSettings']['propertiesToInstrument'])
        excludedProperties = set(request['logSettings']['excludedProperties'])
        assert len(propertiesToInstrument.intersection(
            excludedProperties)) == 0
    return True


def merge_object_requests(python_list):
    """
    Try to merge requests for the same object. Note that
    this isn't that smart and you could still
    end up instrumenting a property twice if you're
    not careful.
    """
    merged_map = {}
    for request in python_list:
        obj = request['object']
        if obj not in merged_map:
            merged_map[obj] = request
        else:
            existing_request = merged_map[obj]
            new_request = request
            if (new_request['instrumentedName']
                    != existing_request['instrumentedName']):
                raise RuntimeError(
                    f'Mismatching instrumentedNames found for object {obj}')
            existing_logSettings = existing_request['logSettings']
            new_logSettings = new_request['logSettings']
            for k, v in existing_logSettings.items():
                # Special case for lists
                if k in list_log_settings:
                    v.extend(new_logSettings[k])
                else:
                    if v != new_logSettings[k]:
                        print(v)
                        print(new_logSettings[k])
                        raise RuntimeError(
                            f'Mismatching logSettings for object {obj}')

    merged_list = list(merged_map.values())
    # Make sure list logSettings are unique
    for request in merged_list:
        for logSetting in list_log_settings:
            request['logSettings'][logSetting] = list(
                set(request['logSettings'][logSetting]))
    return merged_list


def _handle_obj_string(obj_string):
    if obj_string in mdn:
        obj = f'window.{obj_string}.prototype'
        instrumentedName = obj_string
    elif obj_string.startswith('window'):
        obj = obj_string
        instrumentedName = obj_string
    else:
        raise RuntimeError(
            'Requested API not listed in MDN Browser Compat Data')
    return obj, instrumentedName


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
    obj = None
    instrumentedName = None
    logSettings = get_default_log_settings()
    if isinstance(request, str):
        obj, instrumentedName = _handle_obj_string(request)
    elif isinstance(request, dict):
        assert len(request.keys()) == 1
        req = list(request.keys())[0]
        props = request[req]
        obj, instrumentedName = _handle_obj_string(req)
        if isinstance(props, list):
            logSettings['propertiesToInstrument'] = props
        elif isinstance(props, dict):
            for k, v in props.items():
                logSettings[k] = v
        else:
            raise RuntimeError('Invalid settings for object')
    else:
        raise RuntimeError('Invalid input')
    return {
        'object': obj,
        'instrumentedName': instrumentedName,
        'logSettings': logSettings
    }


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
    requests = []
    for request in js_instrument_modules:
        if request in shortcut_specs:
            shortcut_spec = json.loads(open(shortcut_specs[request]).read())
            for sub_request in shortcut_spec:
                requests.append(build_object_from_request(sub_request))
        else:
            requests.append(build_object_from_request(request))
    requests = merge_object_requests(requests)
    validate(requests)
    return python_to_js_string(requests)
