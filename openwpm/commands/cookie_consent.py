# python
from openwpm.commands.types import BaseCommand
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import time
import traceback

from openwpm.commands.utils.cookieButton_rules import rules, commons
from openwpm.commands.utils.cookie_selectors import generate_xpaths


class AcceptCookieConsentCommand(BaseCommand):

    CMP_SELECTORS = [
        "//button[@id='onetrust-accept-btn-handler']",
        "//button[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']",
        "//button[contains(@class,'qc-cmp2-summary-buttons')]"
    ]

    def execute(self, webdriver, browser_params, manager_params, extension_socket):
        start_time = time.time()
        MAX_RUNTIME = 3

        try:
            current_url = webdriver.current_url
            domain = self.get_domain(current_url)

            print(f"[CookieConsent] START | url={current_url} | domain={domain}")

            rule = self.find_matching_rule(domain)

            for xpath in self.CMP_SELECTORS:
                runtime = time.time() - start_time
                if runtime > MAX_RUNTIME:
                    print(f"[CookieConsent] TIMEOUT during CMP selectors | url={current_url} | runtime={runtime:.2f}s")
                    return
                if self.try_click_fast(webdriver, xpath):
                    print(f"[CookieConsent] CMP selector matched | url={current_url} | xpath={xpath} | runtime={runtime:.2f}s")
                    return

            for xpath in generate_xpaths():
                runtime = time.time() - start_time
                if runtime > MAX_RUNTIME:
                    print(f"[CookieConsent] TIMEOUT during keyword fallback | url={current_url} | runtime={runtime:.2f}s")
                    return
                if self.try_click_fast(webdriver, xpath):
                    print(f"[CookieConsent] Keyword selector matched | url={current_url} | runtime={runtime:.2f}s")
                    return

            if rule:
                print(f"[CookieConsent] Domain rule found for {domain}: keys={list(rule.keys())}")
                self.apply_domain_rule(webdriver, rule)
            else:
                print(f"[CookieConsent] No domain rule matched for {domain}")

            total_runtime = time.time() - start_time
            print(f"[CookieConsent] No consent button found | url={current_url} | runtime={total_runtime:.2f}s")

        except Exception as e:
            print(f"[CookieConsent] ERROR | url={webdriver.current_url} | error={str(e)}")
            print(traceback.format_exc())
            return

    def get_domain(self, url):
        netloc = urlparse(url).netloc.lower()
        return netloc.replace("www.", "")

    def find_matching_rule(self, domain):
        for rule_domain in rules:
            if domain.endswith(rule_domain):
                return rules[rule_domain]
        return None

    def click_and_wait(self, webdriver, element, prefer_js=False):
        """
        Attempt to click the provided element. If prefer_js is True, try JS click first.
        After a successful click, wait 5 seconds.
        Returns (clicked: bool, method: str|None)
        method is 'selenium' or 'js'.
        """
        try:
            if prefer_js:
                try:
                    webdriver.execute_script("arguments[0].click();", element)
                    method = "js"
                except Exception:
                    element.click()
                    method = "selenium"
            else:
                try:
                    element.click()
                    method = "selenium"
                except Exception:
                    webdriver.execute_script("arguments[0].click();", element)
                    method = "js"
            # post-click delay
            time.sleep(5)
            return True, method
        except Exception as e:
            print(f"[CookieConsent] click_and_wait failed: {str(e)}")
            return False, None

    def apply_domain_rule(self, webdriver, rule):
        xpaths = rule.get("xpaths", generate_xpaths()) if isinstance(rule, dict) else generate_xpaths()

        # 1) Try Selenium-native clicks (with JS fallback) and wait after each click
        for xp in xpaths:
            try:
                els = webdriver.find_elements(By.XPATH, xp)
                if not els:
                    continue
                for el in els:
                    try:
                        if not el.is_displayed():
                            continue
                        try:
                            print(f"[CookieConsent] Trying click | xpath={xp} for element {el.tag_name} with text '{el.text[:30]}'")
                            clicked, method = self.click_and_wait(webdriver, el, prefer_js=False)
                            if clicked:
                                return {"clicked": True, "xpath": xp, "method": method}
                        except Exception:
                            print(f"[CookieConsent] Click failed, trying JS click | xpath={xp} for element {el.tag_name} with text '{el.text[:30]}'")
                            clicked, method = self.click_and_wait(webdriver, el, prefer_js=True)
                            if clicked:
                                return {"clicked": True, "xpath": xp, "method": method}
                    except Exception:
                        continue
            except Exception:
                continue

        # 2) Fallback: evaluate XPaths in-page via a safe single script with arguments
        js_code = """
        const xpaths = arguments[0];
        for (const xp of xpaths) {
          try {
            const res = document.evaluate(xp, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            const node = res && res.singleNodeValue;
            if (node) {
              if (typeof node.click === 'function') { node.click(); return {clicked: true, xpath: xp, method: 'js-eval'}; }
              const ev = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
              node.dispatchEvent(ev);
              return {clicked: true, xpath: xp, method: 'js-event'};
            }
          } catch (e) {
            // continue
          }
        }
        return {clicked: false};
        """
        try:
            result = webdriver.execute_script(js_code, xpaths)
            if result and result.get("clicked"):
                # page-internal click dispatched; ensure post-click wait
                time.sleep(5)
            return result
        except Exception:
            return {"clicked": False}

    def inject_css(self, webdriver, css):
        webdriver.execute_script("""
            var style = document.createElement('style');
            style.innerHTML = arguments[0];
            document.head.appendChild(style);
        """, css)

    def try_click_fast(self, webdriver, xpath):
        try:
            elements = webdriver.find_elements(By.XPATH, xpath)
            if elements:
                print(f"[CookieConsent] Found {len(elements)} elements for xpath")
            for el in elements:
                if el.is_displayed():
                    # prefer JS for fast attempts (use click_and_wait with prefer_js=True)
                    clicked, _ = self.click_and_wait(webdriver, el, prefer_js=True)
                    if clicked:
                        return True
        except Exception as e:
            print(f"[CookieConsent] XPath failed: {str(e)}")
        return False