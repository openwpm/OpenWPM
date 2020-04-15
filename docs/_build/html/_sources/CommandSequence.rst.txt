The Lifetime of a CommandSequence
==================================

Abstract
---------

The following document aims to completely capture all steps involved in the execution of a `CommandSequence`
in OpenWPM. It's goal is to allow reasoning through the process to discuss changes and tradeoffs.  
The current version of this document ignores all information being saved to the DB from anywhere but the Aggregator.

The Sequence of Execution
--------------------------

1.  :meth:`~automation.TaskManager.TaskManager.execute_command_sequence`
2. :meth:`~automation.TaskManager.TaskManager._start_thread` spawn thread with
3.  :meth:`~automation.TaskManager.TaskManager._issue_command` runs until 
    :class:`~automation.CommandSequence.CommandSequence` is done

    3.1. :meth:`~automation.BrowserManager.BrowserManager` excutes the commands on the other side

