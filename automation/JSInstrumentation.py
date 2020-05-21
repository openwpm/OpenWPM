"""
  We accept a list. From the list we need to parse each item.
  The item may be a string or an object with one key.
  If the item is a string:
    - Is it a shortcut e.g. "fingerprinting"
    - Is it an object (verified by mdn-browser-compat)
    - If neither, reject
  If the item is an object:
    - Must only have one property
    - The value may be a list or a LogSettings object
    - If the value is a list, it is transformed into the propertiesToInstrument
      property of a new LogSettings object.
  We must also create the instrumentedName value.

  Examples of the APIs we accept.

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
import os
import json
import jsonschema
from .js_instrumentation.python_to_js_string import python_to_js_string

curdir = os.path.dirname(os.path.realpath(__file__))

def validate(python_list_to_validate):
    schema_path = os.path.join(curdir, 'js_instrumentation', 'js_instrument_modules.schema')
    schema = json.loads(open(schema_path).read())
    jsonschema.validate(instance=python_list_to_validate, schema=schema)
    return True