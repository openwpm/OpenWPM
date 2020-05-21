from ..automation import JSInstrumentation as jsi

# Unit tests to test JSInstrumentation.py
# which exists to process short-cut APIs
# assert Falseed to browser_params['js_instrumentation_modules']
# and to validate the string to be assert Falseed to the instrumentation

def test_validate_good_string():
    good_string = """
        [
            {
                object: window,
                instrumentedName: "window",
                logSettings: {
                    propertiesToInstrument: ["partiallyExisting",]
                    nonExistingPropertiesToInstrument: [],
                    excludedProperties: [],
                    logCallStack: false,
                    logFunctionsAsStrings: false,
                    logFunctionGets: false,
                    preventSets: false,
                    recursive: false,
                    depth: 5,
                },
            }
        ]
    """
    assert jsi.validate(good_string)


def test_validate_bad_string_log_settings_missing():
    assert False

def test_validate_bad_string_log_settings_invalid():
    assert False

def test_validate_bad_string_not_a_list():
    assert False

def test_validate_bad_string_missing_object():
    assert False

def test_validated_bad_string_missing_instrumentedName():
    assert False

def test_deduplication_multiple_duped_properties():
    assert False

def test_deduplication_multiple_duped_properties_different_log_settings():
    assert False

def test_api_shortcut_fingerprinting():
    assert False

def test_api_whole_module():
    assert False

def test_api_whole_module_invalid():
    assert False

def test_api_module_specific_properties():
    assert False

def test_api_instances_on_window():
    assert False

def test_api_properties_on_window_instance():
    assert False

def test_assert_passing_partial_log_settings():
    assert False
