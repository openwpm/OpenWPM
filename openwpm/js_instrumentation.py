import json
import os
from typing import Any, Dict, List

import jsonschema

curdir = os.path.dirname(os.path.realpath(__file__))
schema_path = os.path.join(
    curdir, os.pardir, "schemas", "js_instrument_settings.schema.json"
)

list_log_settings = [
    "propertiesToInstrument",
    "nonExistingPropertiesToInstrument",
    "excludedProperties",
]
shortcut_specs = {
    "collection_fingerprinting": os.path.join(
        curdir, "js_instrumentation_collections", "fingerprinting.json"
    )
}


def _validate(python_list_to_validate):
    with open(schema_path, "r") as f:
        schema = json.loads(f.read())
    jsonschema.validate(instance=python_list_to_validate, schema=schema)
    # Check properties to instrument and excluded properties don't collide
    for setting in python_list_to_validate:
        propertiesToInstrument = setting["logSettings"]["propertiesToInstrument"]
        if propertiesToInstrument is not None:
            propertiesToInstrument = set(propertiesToInstrument)
            excludedProperties = set(setting["logSettings"]["excludedProperties"])
            if len(propertiesToInstrument.intersection(excludedProperties)) != 0:
                raise ValueError(
                    f"excludedProperties and \
                    propertiesToInstrument collide. This \
                    may have occurred after a merge. \
                    Setting with collision: {setting}."
                )
    return True


def _merge_settings(python_list):
    """
    Try to merge settings for the same object. Note that
    this isn't that smart and you could still
    end up instrumenting a property twice if you're
    not careful.
    """
    merged_map = {}
    for setting in python_list:
        obj = setting["object"]
        if obj not in merged_map:
            merged_map[obj] = setting
        else:
            existing_setting = merged_map[obj]
            new_setting = setting
            if new_setting["instrumentedName"] != existing_setting["instrumentedName"]:
                raise RuntimeError(
                    f"Mismatching instrumentedNames found for object {obj}"
                )
            existing_logSettings = existing_setting["logSettings"]
            new_logSettings = new_setting["logSettings"]
            for k, v in existing_logSettings.items():
                # Special case for lists
                if k in list_log_settings:
                    new_val = new_logSettings[k]
                    if (v is None) or (new_val is None):
                        raise RuntimeError(f"Mismatching logSettings for object {obj}")
                    else:
                        v.extend(new_logSettings[k])
                else:
                    if v != new_logSettings[k]:
                        print(v)
                        print(new_logSettings[k])
                        raise RuntimeError(f"Mismatching logSettings for object {obj}")

    merged_list = list(merged_map.values())
    # Make sure list logSettings are unique
    for setting in merged_list:
        for logSetting in list_log_settings:
            list_setting_value = setting["logSettings"][logSetting]
            if list_setting_value is None:
                continue
            else:
                if None in list_setting_value:
                    raise RuntimeError(f"Mismatching logSettings for object {obj}")
                else:
                    # Dedupe
                    setting["logSettings"][logSetting] = list(
                        set(setting["logSettings"][logSetting])
                    )
    return merged_list


def _handle_obj_string(obj_string):
    if obj_string.startswith("window"):
        obj = obj_string
        instrumentedName = obj_string
    else:
        obj = f"window['{obj_string}'].prototype"
        instrumentedName = obj_string
    return obj, instrumentedName


def _build_full_settings_object(setting):
    """
    We need to build a valid object from each setting.

    The item may be a string or an object with one key.
    If the item is a string:
      - Is it a shortcut e.g. "collection_fingerprinting"
      - Is it an object (verified by mdn-browser-compat)
      - If neither, reject
    If the item is an object:
      - Must only have one property
      - The value may be a list or a LogSettings object
      - If the value is a list, it is transformed into the
        propertiesToInstrument property of a new LogSettings object.
    We must also create the instrumentedName value.
    """
    logSettings = get_default_log_settings()

    if isinstance(setting, str):
        obj, instrumentedName = _handle_obj_string(setting)

    elif isinstance(setting, dict):

        if len(setting.keys()) != 1:
            raise ValueError(
                f"Invalid settings request. \
                Settings item is a dictionary with more \
                than one key. Received {setting}."
            )

        setting_key = list(setting.keys())[0]
        props = setting[setting_key]
        obj, instrumentedName = _handle_obj_string(setting_key)
        if isinstance(props, list):
            logSettings["propertiesToInstrument"] = props
        elif isinstance(props, dict):
            for k, v in props.items():
                logSettings[k] = v
        else:
            raise ValueError(
                f"Invalid settings request. \
                Setting was a dictionary. Settings value \
                must be a list or a dictionary. Received \
                {setting}."
            )
    else:
        raise ValueError(
            f"Invalid settings request. \
            Must be a string or a dictionary. \
            Received {setting}."
        )

    return {
        "object": obj,
        "instrumentedName": instrumentedName,
        "logSettings": logSettings,
    }


def get_default_log_settings():
    """Returns a dictionary of default instrumentation settings.

    The set of instrumentation settings to be used when
    others are not provided. The specification of these
    settings is detailed in ``js_instrument_settings.schema``.


    Returns
    -------
    dict
        Dictionary of default instrumentation settings
    """
    return {
        "propertiesToInstrument": [],
        "nonExistingPropertiesToInstrument": [],
        "excludedProperties": [],
        "logCallStack": False,
        "logFunctionsAsStrings": False,
        "logFunctionGets": False,
        "preventSets": False,
        "recursive": False,
        "depth": 5,
    }


def clean_js_instrumentation_settings(
    user_requested_settings: List[Any],
) -> List[Dict[str, Any]]:
    """Convert user input JSinstrumentation settings to full settings object.

    Accepts a list. From the list we need to parse each item.
    Examples of the settings we accept.

    ```
    // Collections
    "collection_fingerprinting",
    // APIs, with or without settings details
    "XMLHttpRequest",
    {"XMLHttpRequest": {"excludedProperties": ["send"]}},
    // APIs with shortcut to includedProperties
    {"Prop1": ["hi"], "Prop2": ["hi2"]},
    {"XMLHttpRequest": ["send"]},
    "Storage",
    // Specific instances on window
    {"window.document": ["cookie", "referrer"]},
    {"window": ["name", "localStorage", "sessionStorage"]}
    ```

    Parameters
    ----------
    user_requested_settings: list
        The list of JS Instrumentation settings requested by
        the user, which may include syntactic shortcuts as outlined
        in method docs.


    Returns
    -------
    list
        List of all requested JS Instrumentation with all settings
        applied. Has been nominally de-duped and validated against
        `js_instrument_settings.schema``.

    """
    if not isinstance(user_requested_settings, list):
        raise TypeError(
            f"js_instrumentation_settings must be a list. \
              Received {user_requested_settings}"
        )
    settings = []
    for setting in user_requested_settings:
        if isinstance(setting, str) and (setting in shortcut_specs):
            with open(shortcut_specs[setting], "r") as f:
                shortcut_spec = json.loads(f.read())
            for sub_setting in shortcut_spec:
                settings.append(_build_full_settings_object(sub_setting))
        else:
            settings.append(_build_full_settings_object(setting))
    settings = _merge_settings(settings)
    _validate(settings)
    return settings
