"""The default prefs take effect in a fresh OpenWPM profile."""

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.utilities import db_utils

# Initialising SafeBrowsing ourselves is a no-op if Firefox already did, and
# makes the table check meaningful even if it has not yet. The tables checked
# are the shipped defaults, i.e. what would be registered without our prefs.
_PROBE_JS = """
const { SafeBrowsing } = ChromeUtils.importESModule(
  "resource://gre/modules/SafeBrowsing.sys.mjs"
);
SafeBrowsing.init();
const listManager = Cc["@mozilla.org/url-classifier/listmanager;1"].getService(
  Ci.nsIUrlListManager
);
const defaults = Services.prefs.getDefaultBranch("");
const tables = ["google", "google4", "google5", "mozilla"].flatMap(p =>
  defaults
    .getCharPref(`browser.safebrowsing.provider.${p}.lists`, "")
    .split(",")
    .map(t => t.trim())
    .filter(Boolean)
);
return {
  normandy: Services.prefs.getBoolPref("app.normandy.enabled", true),
  safebrowsingUpdate: Services.prefs.getBoolPref(
    "browser.safebrowsing.update.enabled",
    true
  ),
  checkedTables: tables.length,
  updatingFeatures: SafeBrowsing.features.filter(f => f.update).map(f => f.name),
  tablesWithUpdateUrl: tables.filter(t => listManager.getUpdateUrl(t) !== ""),
};
"""


class AssertPrefsInEffectCommand(BaseCommand):
    def execute(self, webdriver, browser_params, manager_params, extension_socket):
        # Chrome context needs geckodriver's --allow-system-access, which
        # deploy_firefox passes.
        with webdriver.context(webdriver.CONTEXT_CHROME):
            state = webdriver.execute_script(_PROBE_JS)
        assert state["checkedTables"] > 0, state
        assert state == {
            "normandy": False,
            "safebrowsingUpdate": False,
            "checkedTables": state["checkedTables"],
            "updatingFeatures": [],
            "tablesWithUpdateUrl": [],
        }, state


def test_normandy_and_safebrowsing_updates_off(
    default_params, task_manager_creator, server
):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager, db = task_manager_creator((manager_params, browser_params[:1]))
    with manager:
        cs = CommandSequence(url=server.base)
        cs.get()
        cs.append_command(AssertPrefsInEffectCommand())
        manager.execute_command_sequence(cs)

    rows = db_utils.query_db(
        db,
        "SELECT command, command_status, error FROM crawl_history",
    )
    assert rows
    for row in rows:
        assert row["command_status"] == "ok", row["error"]
