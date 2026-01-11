from openwpm.commands.types import BaseCommand
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AcceptCookieConsentCommand(BaseCommand):
    def execute(
            self,
            webdriver,
            browser_params,
            manager_params,
            extension_socket
    ):
        try:
            wait = WebDriverWait(webdriver, 5)

            selectors = [
                # English (US/UK)
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept and close')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i accept')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow all')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow cookies')]",

                # Spanish (Spain / Latin America)
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceptar')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceptar todo')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceptar cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceptar y cerrar')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceptar y continuar')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'estoy de acuerdo')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'de acuerdo')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permitir')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permitir cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceptar siempre')]",

                # Portuguese (Portugal / Brazil)
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceitar')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceitar tudo')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceitar cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'eu aceito')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceito')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'concordo')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'concordar')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permitir')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permitir cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permitir tudo')]",

                # French
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accepter')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tout accepter')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accepter les cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"j'accepte\")]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'je suis daccord')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'je suis d\\'accord')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autoriser')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autoriser cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autoriser tout')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",

                # German
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'akzeptieren')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'annehmen')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'alle akzeptieren')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'cookies akzeptieren')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'zustimmen')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'einverstanden')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'erlauben')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'erlauben alle')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'bestätigen')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ', 'abcdefghijklmnopqrstuvwxyzäöüß'), 'ok')]",

                # Italian
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta tutto')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta i cookie')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetto')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sono daccordo')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autorizza')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consenti')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consenti tutto')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta sempre')]",

                # Dutch
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accepteren')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'alles accepteren')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cookies accepteren')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ik ga akkoord')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akkoord')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'toestaan')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sta toe')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'toestaan cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'toestaan alles')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",

                # Polish
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akceptuj')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zaakceptuj')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akceptuj wszystko')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akceptuj ciasteczka')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zgadzam sie')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zgoda')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pozwol')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pozwol ciasteczka')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zatwierdz')]",

                # Swedish
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acceptera')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acceptera alla')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acceptera cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'godkänn')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'jag godkänner')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tillåt')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tillåt alla')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tillåt cookies')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'okej')]",
                "//*[contains(translate(string(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acceptera alltid')]"
            ]

            for sel in selectors:
                try:
                    button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, sel))
                    )
                    button.click()
                    print(f"Cookie consent clicked using selector: {sel} on url: {webdriver.current_url}")
                    break
                except Exception:
                    continue

        except Exception:
            pass
