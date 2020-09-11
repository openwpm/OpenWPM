import pytest
from jsonschema.exceptions import ValidationError

from ..automation import js_instrumentation as jsi

pytestmark = pytest.mark.pyonly


def _no_whitespace(x):
    return "".join(x.split())


# Test function that converts our python
# objects to our JS string


def test_python_to_js_lower_true_false():
    inpy = [
        {
            "object": "window",
            "logSettings": {
                "logCallStack": False,
                "preventSets": True,
            },
        }
    ]
    expected_out = _no_whitespace(
        """
    [{
        "object": window,
        "logSettings": {
            "logCallStack": false,
            "preventSets": true
        }
    }]
    """
    )
    actual_out = _no_whitespace(jsi._python_to_js_string(inpy))
    assert actual_out == expected_out


def test_python_to_js_no_quote_object():
    inpy = [{"object": "window", "logSettings": {}}]
    expected_out = _no_whitespace('[{"object": window, "logSettings": {}}]')
    actual_out = _no_whitespace(jsi._python_to_js_string(inpy))
    assert actual_out == expected_out


def test_python_to_js_no_quote_object_two_matching_objects():
    inpy = [
        {"object": "window", "logSettings": {}},
        {"object": "window", "logSettings": {}},
        {"object": "window2", "logSettings": {}},
    ]
    expected_out = _no_whitespace(
        """[
        {"object": window, "logSettings": {}},
        {"object": window, "logSettings": {}},
        {"object": window2, "logSettings": {}}
    ]"""
    )
    actual_out = _no_whitespace(jsi._python_to_js_string(inpy))
    assert actual_out == expected_out


# Test our validation
@pytest.fixture
def default_log_settings():
    return jsi.get_default_log_settings()


def test_validate_good(default_log_settings):
    good_input = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": default_log_settings,
        }
    ]
    assert jsi._validate(good_input)


def test_validate_bad__log_settings_missing(default_log_settings):
    log_keys = default_log_settings.keys()
    for log_key in log_keys:
        print("Testing for missing", log_key)
        log_settings = default_log_settings.copy()
        log_settings.pop(log_key)
        bad_input = [
            {
                "object": "window",
                "instrumentedName": "window",
                "logSettings": log_settings,
            }
        ]
        with pytest.raises(ValidationError):
            jsi._validate(bad_input),


def test_validate_bad__log_settings_invalid(default_log_settings):
    log_settings = default_log_settings.copy()
    log_settings["recursive"] = "yes, please"
    bad_input = [
        {"object": "window", "instrumentedName": "window", "logSettings": log_settings}
    ]
    with pytest.raises(ValidationError):
        assert jsi._validate(bad_input)


def test_validate_bad__not_a_list(default_log_settings):
    bad_input = {
        "object": "window",
        "instrumentedName": "window",
        "logSettings": default_log_settings,
    }
    with pytest.raises(ValidationError):
        assert jsi._validate(bad_input)


def test_validate_bad__missing_object(default_log_settings):
    bad_input = [{"instrumentedName": "window", "logSettings": default_log_settings}]
    with pytest.raises(ValidationError):
        assert jsi._validate(bad_input)


def test_validated_bad__missing_instrumentedName(default_log_settings):
    bad_input = [{"object": "window", "logSettings": default_log_settings}]
    with pytest.raises(ValidationError):
        assert jsi._validate(bad_input)


def test_merge_and_validate_multiple_overlap_properties_to_instrument_properties_to_exclude(
    default_log_settings,
):  # noqa
    log_settings_1 = default_log_settings.copy()
    log_settings_2 = default_log_settings.copy()
    log_settings_1["propertiesToInstrument"] = ["name", "place"]
    log_settings_2["excludedProperties"] = ["name"]
    dupe_input = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_1,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_2,
        },
    ]
    merged = jsi._merge_settings(dupe_input)
    with pytest.raises(ValueError):
        jsi._validate(merged)


def test_merge_and_validate_multiple_overlap_properties(default_log_settings):
    log_settings_1 = default_log_settings.copy()
    log_settings_2 = default_log_settings.copy()
    log_settings_merge = default_log_settings.copy()
    log_settings_1["propertiesToInstrument"] = ["name", "place"]
    log_settings_2["propertiesToInstrument"] = ["localStorage"]
    log_settings_merge["propertiesToInstrument"] = ["name", "place", "localStorage"]
    dupe_input = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_1,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_2,
        },
    ]
    expected_de_dupe_output = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_merge,
        },
    ]
    actual_output = jsi._merge_settings(dupe_input)
    for key in ["object", "instrumentedName"]:
        assert expected_de_dupe_output[0][key] == actual_output[0][key]
    assert set(expected_de_dupe_output[0]["logSettings"]) == set(
        actual_output[0]["logSettings"]
    )


def test_merge_when_log_settings_is_null(default_log_settings):
    # It's valid to send None to log settings.
    # In that case, merging with another list would be a
    # mismatch. But just asking for null should be allowed.

    log_settings_some = default_log_settings.copy()
    log_settings_none = default_log_settings.copy()
    log_settings_some["propertiesToInstrument"] = ["name", "place"]
    log_settings_none["propertiesToInstrument"] = None
    input_1 = [
        {
            "object": "window.document",
            "instrumentedName": "window",
            "logSettings": log_settings_none,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_some,
        },
    ]
    actual_output = jsi._merge_settings(input_1)
    assert actual_output == input_1

    input_2 = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_some,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_none,
        },
    ]
    with pytest.raises(RuntimeError) as error:
        jsi._merge_settings(input_2)
    assert "Mismatching logSettings" in str(error.value)

    input_3 = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_none,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_some,
        },
    ]
    with pytest.raises(RuntimeError) as error:
        jsi._merge_settings(input_3)
    assert "Mismatching logSettings" in str(error.value)


def test_merge_diff_instrumented_names(default_log_settings):
    dupe_input = [
        {
            "object": "window",
            "instrumentedName": "window1",
            "logSettings": default_log_settings,
        },
        {
            "object": "window",
            "instrumentedName": "window2",
            "logSettings": default_log_settings,
        },
    ]
    with pytest.raises(RuntimeError) as error:
        jsi._merge_settings(dupe_input)
    assert "Mismatching instrumentedNames" in str(error.value)


def test_merge_multiple_duped_properties(default_log_settings):
    dupe_input = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": default_log_settings,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": default_log_settings,
        },
    ]
    expected_de_dupe_output = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": default_log_settings,
        },
    ]
    assert jsi._merge_settings(dupe_input) == expected_de_dupe_output


def test_merge_multiple_duped_properties_different_log_settings(
    default_log_settings,
):  # noqa
    log_settings_1 = default_log_settings.copy()
    log_settings_2 = default_log_settings.copy()
    log_settings_1["depth"] = 3
    log_settings_2["depth"] = 4
    dupe_input = [
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_1,
        },
        {
            "object": "window",
            "instrumentedName": "window",
            "logSettings": log_settings_2,
        },
    ]
    with pytest.raises(RuntimeError) as error:
        jsi._merge_settings(dupe_input)
    assert "Mismatching logSettings for object" in str(error.value)


def test_api_whole_module(default_log_settings):
    shortcut_input = "XMLHttpRequest"
    expected_output = {
        "object": "window['XMLHttpRequest'].prototype",
        "instrumentedName": "XMLHttpRequest",
        "logSettings": default_log_settings,
    }
    actual_output = jsi._build_full_settings_object(shortcut_input)
    assert actual_output == expected_output


def test_api_two_keys_in_shortcut():
    shortcut_input = {"k1": [], "k2": []}
    with pytest.raises(ValueError):
        jsi._build_full_settings_object(shortcut_input)


def test_api_instances_on_window(default_log_settings):
    shortcut_input = "window.navigator"
    expected_output = {
        "object": "window.navigator",
        "instrumentedName": "window.navigator",
        "logSettings": default_log_settings,
    }
    actual_output = jsi._build_full_settings_object(shortcut_input)
    assert actual_output == expected_output


def test_api_instances_on_window_with_properties(default_log_settings):
    log_settings = default_log_settings.copy()
    log_settings["propertiesToInstrument"] = ["name", "localStorage"]
    shortcut_input = {"window": ["name", "localStorage"]}
    expected_output = {
        "object": "window",
        "instrumentedName": "window",
        "logSettings": log_settings,
    }
    actual_output = jsi._build_full_settings_object(shortcut_input)
    assert actual_output == expected_output


def test_api_module_specific_properties(default_log_settings):
    log_settings = default_log_settings.copy()
    log_settings["propertiesToInstrument"] = ["send"]
    shortcut_input = {"XMLHttpRequest": ["send"]}
    expected_output = {
        "object": "window['XMLHttpRequest'].prototype",
        "instrumentedName": "XMLHttpRequest",
        "logSettings": log_settings,
    }
    actual_output = jsi._build_full_settings_object(shortcut_input)
    assert actual_output == expected_output


def test_api_passing_partial_log_settings(default_log_settings):
    log_settings = default_log_settings.copy()
    log_settings["excludedProperties"] = ["send"]
    log_settings["recursive"] = True
    log_settings["depth"] = 2
    shortcut_input = {
        "XMLHttpRequest": {
            "excludedProperties": ["send"],
            "recursive": True,
            "depth": 2,
        }
    }
    expected_output = {
        "object": "window['XMLHttpRequest'].prototype",
        "instrumentedName": "XMLHttpRequest",
        "logSettings": log_settings,
    }
    actual_output = jsi._build_full_settings_object(shortcut_input)
    assert actual_output == expected_output


def test_api_collection_fingerprinting():
    # This is a very crude test, there are other tests to
    # check fingeprinting instrumentation in more detail
    shortcut_input = ["collection_fingerprinting"]
    output = jsi.clean_js_instrumentation_settings(shortcut_input)
    assert "window.document" in output
    assert "window['AudioContext'].prototype" in output


def test_complete_pass():
    shortcut_input = [{"window": {"recursive": True}}]
    output = jsi.clean_js_instrumentation_settings(shortcut_input)
    assert '"recursive": true' in output
    assert '"instrumentedName": "window"' in output
