""" Set prefs and load extensions in Firefox """
import shutil
import sys
import os

def privacy(browser_params, fp, root_dir, browser_profile_path):
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions
    """

    # Turns on Do Not Track
    if browser_params['donottrack']:
        fp.set_preference("privacy.donottrackheader.enabled", True)
        fp.set_preference("privacy.donottrackheader.value", 1)

    # Sets the third party cookie setting
    if browser_params['tp_cookies'].lower() == 'never':
        fp.set_preference("network.cookie.cookieBehavior", 1)
    elif browser_params['tp_cookies'].lower() == 'from_visited':
        fp.set_preference("network.cookie.cookieBehavior", 3)
    else:  # always allow third party cookies
        fp.set_preference("network.cookie.cookieBehavior", 0)

    # Tracking Protection
    if browser_params['tracking-protection']:
        print "ERROR: Tracking Protection doesn't seem to work in Firefox 41 with selenium."
        print "       It does work in 42 Beta. This will be enabled once that lands in release."
        print "       Press Ctrl+C to exit"
        sys.exit(1)
        #fp.set_preference('privacy.trackingprotection.enabled', True)

    # Load Ghostery - Enable all blocking
    if browser_params['ghostery']:
        fp.add_extension(extension=os.path.join(root_dir,'firefox_extensions/ghostery/ghostery-5.4.6.xpi'))
        os.makedirs(browser_profile_path+'jetpack/firefox@ghostery.com/simple-storage/')
        src = os.path.join(root_dir,'firefox_extensions/ghostery/store.json') # settings - block all trackers/cookies
        dst = os.path.join(browser_profile_path,'jetpack/firefox@ghostery.com/simple-storage/store.json')
        shutil.copy(src,dst)
    
    # Enable HTTPS Everywhere
    if browser_params['https-everywhere']:
        fp.add_extension(extension=os.path.join(root_dir,'firefox_extensions/https-everywhere-5.0.7.xpi'))
        fp.set_preference("extensions.https_everywhere.firstrun_context_menu", True)
        fp.set_preference("extensions.https_everywhere.prefs_version", 1)
        fp.set_preference("extensions.https_everywhere.toolbar_hint_shown", True)
        fp.set_preference("extensions.https_everywhere._observatory.popup_shown", True)
        fp.set_preference("extensions.https_everywhere._observatory.clean_config", True)

    # Enable AdBlock Plus - Uses "Easy List" by default
    # "Allow some non-intrusive advertising" disabled
    if browser_params['adblock-plus']:
        fp.add_extension(extension=os.path.join(root_dir,'firefox_extensions/adblock-plus-2.6.11.xpi'))
        fp.set_preference('extensions.adblockplus.subscriptions_exceptionsurl', '')
        fp.set_preference('extensions.adblockplus.suppress_first_run_page', True)

def optimize_prefs(fp):
    """
    Disable various features and checks the browser will do on startup.
    Some of these (e.g. disabling the newtab page) are required to prevent
    extraneous data in the proxy.
    """
    # Startup / Speed
    fp.set_preference('browser.shell.checkDefaultBrowser', False)
    fp.set_preference("browser.slowStartup.notificationDisabled", True)
    fp.set_preference("browser.slowStartup.maxSamples", 0)
    fp.set_preference("browser.slowStartup.samples", 0)
    fp.set_preference('extensions.checkCompatibility.nightly', False)
    fp.set_preference('browser.rights.3.shown', True)
    fp.set_preference("reader.parse-on-load.enabled", False)
    fp.set_preference('browser.pagethumbnails.capturing_disabled', True)
    fp.set_preference('devtools.profiler.enabled', False)

    # Disable health reports / telemetry / crash reports
    fp.set_preference("datareporting.policy.dataSubmissionEnabled", False) #FF41+ Master Switch
    fp.set_preference('datareporting.healthreport.uploadEnabled', False)
    fp.set_preference("datareporting.healthreport.service.enabled", False)
    fp.set_preference('toolkit.telemetry.enabled', False)
    fp.set_preference("toolkit.telemetry.unified", False)
    fp.set_preference("breakpad.reportURL", "")
    fp.set_preference("dom.ipc.plugins.flash.subprocess.crashreporter.enabled", False)
    
    # Predictive Actions / Prefetch
    fp.set_preference('network.seer.enabled', False)
    fp.set_preference('network.dns.disablePrefetch', True)
    fp.set_preference('network.prefetch-next', False)
    fp.set_preference("browser.search.suggest.enabled", False)
    fp.set_preference("network.http.speculative-parallel-limit", 0)
    fp.set_preference("keyword.enabled", False) # location bar using search

    # Disable pinging Mozilla for geoip
    fp.set_preference('browser.search.geoip.url', '')
    fp.set_preference("browser.search.countryCode", "US")
    fp.set_preference("browser.search.region", "US")

    # Disable auto-updating
    fp.set_preference("app.update.enabled", False) # browser
    fp.set_preference("app.update.url", "") # browser
    fp.set_preference("browser.search.update", False) # search
    fp.set_preference("extensions.update.enabled", False) # extensions
    fp.set_preference("extensions.update.autoUpdateDefault", False) # addons
    fp.set_preference("extensions.getAddons.cache.enabled", False) 
    fp.set_preference("lightweightThemes.update.enabled", False) # Personas

    # Disable Safebrowsing
    fp.set_preference("browser.safebrowsing.enabled", False)
    fp.set_preference("browser.safebrowsing.malware.enabled", False)
    fp.set_preference("browser.safebrowsing.downloads.enabled", False)
    fp.set_preference("browser.safebrowsing.downloads.remote.enabled", False)
    fp.set_preference('security.OCSP.enabled', 0)

    # Disable Experiments
    fp.set_preference("experiments.enabled", False)
    fp.set_preference("experiments.manifest.uri", "")
    fp.set_preference("experiments.supported", False)
    fp.set_preference("experiments.activeExperiment", False)
    fp.set_preference("network.allow-experiments", False)

    # Disable pinging Mozilla for newtab
    fp.set_preference("browser.newtabpage.directory.ping", "")
    fp.set_preference("browser.newtabpage.directory.source", "")
    fp.set_preference("browser.newtabpage.enabled", False)
    fp.set_preference("browser.newtabpage.enhanced", False)
    fp.set_preference("browser.newtabpage.introShown", True)

    # Disable Pocket
    fp.set_preference("browser.pocket.enabled", False)

    # Disable Hello
    fp.set_preference("loop.enabled", False)
