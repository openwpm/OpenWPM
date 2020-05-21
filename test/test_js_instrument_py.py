import pytest
from jsonschema.exceptions import ValidationError

from ..automation import JSInstrumentation as jsi

pytestmark = pytest.mark.pyonly


def _no_whitespace(x):
    return "".join(x.split())

# Test function that converts our python
# objects to our JS string


def test_python_to_js_lower_true_false():
    inpy = [{
        'object': 'window',
        'logSettings': {
            'logCallStack': False,
            'preventSets': True,
        }
    }]
    expected_out = _no_whitespace("""
    [{
        "object": window,
        "logSettings": {
            "logCallStack": false,
            "preventSets": true
        }
    }]
    """)
    actual_out = _no_whitespace(jsi.python_to_js_string(inpy))
    assert actual_out == expected_out


def test_python_to_js_no_quote_object():
    inpy = [{'object': 'window', 'logSettings': {}}]
    expected_out = _no_whitespace('[{"object": window, "logSettings": {}}]')
    actual_out = _no_whitespace(jsi.python_to_js_string(inpy))
    assert actual_out == expected_out


def test_python_to_js_no_quote_object_two_matching_objects():
    inpy = [
        {'object': 'window', 'logSettings': {}},
        {'object': 'window', 'logSettings': {}},
        {'object': 'window2', 'logSettings': {}}
    ]
    expected_out = _no_whitespace("""[
        {"object": window, "logSettings": {}},
        {"object": window, "logSettings": {}},
        {"object": window2, "logSettings": {}}
    ]""")
    actual_out = _no_whitespace(jsi.python_to_js_string(inpy))
    assert actual_out == expected_out


# Test our validation
@pytest.fixture
def default_log_settings():
    return jsi.get_default_log_settings()


def test_validate_good(default_log_settings):
    good_input = [
        {
            'object': 'window',
            'instrumentedName': "window",
            'logSettings': default_log_settings
        }
    ]
    assert jsi.validate(good_input)


def test_validate_bad__log_settings_missing(default_log_settings):
    log_keys = default_log_settings.keys()
    for log_key in log_keys:
        print('Testing for missing', log_key)
        log_settings = default_log_settings.copy()
        log_settings.pop(log_key)
        bad_input = [
            {
                'object': 'window',
                'instrumentedName': "window",
                'logSettings': log_settings
            }
        ]
        with pytest.raises(ValidationError):
            jsi.validate(bad_input),


def test_validate_bad__log_settings_invalid(default_log_settings):
    log_settings = default_log_settings.copy()
    log_settings['recursive'] = 'yes, please'
    bad_input = [
        {
            'object': 'window',
            'instrumentedName': "window",
            'logSettings': log_settings
        }
    ]
    with pytest.raises(ValidationError):
        assert jsi.validate(bad_input)


def test_validate_bad__not_a_list(default_log_settings):
    bad_input = {
        'object': 'window',
        'instrumentedName': "window",
        'logSettings': default_log_settings
    }
    with pytest.raises(ValidationError):
        assert jsi.validate(bad_input)


def test_validate_bad__missing_object(default_log_settings):
    bad_input = [{
        'instrumentedName': "window",
        'logSettings': default_log_settings
    }]
    with pytest.raises(ValidationError):
        assert jsi.validate(bad_input)


def test_validated_bad__missing_instrumentedName(default_log_settings):
    bad_input = [{
        'object': 'window',
        'logSettings': default_log_settings
    }]
    with pytest.raises(ValidationError):
        assert jsi.validate(bad_input)


def test_merge_and_validate_multiple_overlap_properties_to_instrument_properties_to_exclude(default_log_settings):  # noqa
    log_settings_1 = default_log_settings.copy()
    log_settings_2 = default_log_settings.copy()
    log_settings_1['propertiesToInstrument'] = ['name', 'place']
    log_settings_2['excludedProperties'] = ['name']
    dupe_input = [
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': log_settings_1
        },
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': log_settings_2
        },
    ]
    merged = jsi.merge_object_requests(dupe_input)
    with pytest.raises(AssertionError):
        jsi.validate(merged)


def test_merge_diff_instrumented_names(default_log_settings):
    dupe_input = [
        {
            'object': 'window',
            'instrumentedName': 'window1',
            'logSettings': default_log_settings
        },
        {
            'object': 'window',
            'instrumentedName': 'window2',
            'logSettings': default_log_settings
        },
    ]
    with pytest.raises(RuntimeError) as error:
        jsi.merge_object_requests(dupe_input)
    assert 'Mismatching instrumentedNames' in str(error.value)


def test_merge_multiple_duped_properties(default_log_settings):
    dupe_input = [
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': default_log_settings
        },
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': default_log_settings
        },
    ]
    expected_de_dupe_output = [
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': default_log_settings
        },
    ]
    assert jsi.merge_object_requests(dupe_input) == expected_de_dupe_output


def test_merge_multiple_duped_properties_different_log_settings(default_log_settings):  # noqa
    log_settings_1 = default_log_settings.copy()
    log_settings_2 = default_log_settings.copy()
    log_settings_1['depth'] = 3
    log_settings_2['depth'] = 4
    dupe_input = [
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': log_settings_1
        },
        {
            'object': 'window',
            'instrumentedName': 'window',
            'logSettings': log_settings_2
        },
    ]
    with pytest.raises(RuntimeError) as error:
        jsi.merge_object_requests(dupe_input)
    assert 'Mismatching logSettings for object' in str(error.value)


def test_api_whole_module(default_log_settings):
    shortcut_input = ["XMLHttpRequest"]
    expected_output = [{

    }]


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


def test_api_shortcut_fingerprinting():
    assert False
