from OpenWPM.automation import CommandSequence, TaskManager


def test_valid_label_check():
    # Test if the label provided as function argument is legitimate
    # Browsers should work normally but label is no longer useful
    sites = ['http://www.example.com',
             'http://www.google.com',
             'http://www.princeton.edu/']

    manager_params, browser_params = TaskManager.load_default_params(3)
    # prioritizing 2nd browser
    browser_params[1]['donottrack'] = True
    browser_params[1]['label'] = ['donottrack']

    manager = TaskManager.TaskManager(manager_params, browser_params)
    # initializing label function argument with a
    # field not present in browser params
    label = 'testcase'
    # Visits the sites
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site, reset=True)
        command_sequence.get(sleep=3, timeout=60)
        # Testing with a wrong label
        manager.execute_command_sequence(command_sequence, label=label)

    manager.close()
    # Throwing an assertion when the label is illegitimate
    assert label in browser_params[0].keys(), \
        "Provided label is not in browser parameters"


def test_pick_label_config():
    # Test to see if the correct label results in picking
    # the browser based on browser configuration
    sites = ['http://www.example.com',
             'http://www.google.com',
             'http://www.princeton.edu/']

    manager_params, browser_params = TaskManager.load_default_params(3)
    # prioritizing 2nd browser
    browser_params[1]['donottrack'] = True
    browser_params[1]['label'] = ['donottrack']

    manager = TaskManager.TaskManager(manager_params, browser_params)

    # Visits the sites
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site, reset=True)
        command_sequence.get(sleep=3, timeout=60)
        # legitimate label without index should result in a
        # browser being picked based on label configuration
        manager.execute_command_sequence(command_sequence, label='donottrack')

    manager.close()


def test_index_overwriting_label():
    # Test to check if index overwrites label
    sites = ['http://www.example.com',
             'http://www.google.com',
             'http://www.princeton.edu/']

    manager_params, browser_params = TaskManager.load_default_params(3)
    # prioritizing 2nd browser
    browser_params[1]['donottrack'] = True
    browser_params[1]['label'] = ['donottrack']

    manager = TaskManager.TaskManager(manager_params, browser_params)

    # Visits the sites
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site, reset=True)
        command_sequence.get(sleep=3, timeout=60)
        # First browser should take precedence over the label of 2nd browser
        manager.execute_command_sequence(command_sequence, index=0,
                                         label='donottrack')

    manager.close()


url = 'http://www.google.com'
cs = CommandSequence.CommandSequence(url)
cs.get(sleep=0, timeout=60)
cs.run_custom_function(test_valid_label_check())
cs.run_custom_function(test_pick_label_config())
cs.run_custom_function(test_index_overwriting_label())
