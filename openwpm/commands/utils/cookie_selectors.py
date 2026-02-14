import re

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ"
LOWER = "abcdefghijklmnopqrstuvwxyzäöüß"

KEYWORDS = [
    # English
    "accept", "accept all", "accept cookies", "accept and close",
    "agree", "i accept", "i agree", "allow", "allow all", "allow cookies",

    # Spanish
    "aceptar", "aceptar todo", "aceptar cookies",
    "aceptar y cerrar", "aceptar y continuar",
    "estoy de acuerdo", "de acuerdo", "permitir",
    "permitir cookies", "aceptar siempre",

    # Portuguese
    "aceitar", "aceitar tudo", "aceitar cookies",
    "eu aceito", "aceito", "concordo", "concordar",
    "permitir", "permitir cookies", "permitir tudo",

    # French
    "accepter", "tout accepter", "accepter les cookies",
    "j'accepte", "je suis daccord", "autoriser",
    "autoriser cookies", "autoriser tout",

    # German
    "akzeptieren", "annehmen", "alle akzeptieren",
    "cookies akzeptieren", "zustimmen",
    "einverstanden", "erlauben", "bestätigen",

    # Italian
    "accetta", "accetta tutto", "accetta i cookie",
    "accetto", "sono daccordo", "autorizza",
    "consenti", "consenti tutto",

    # Dutch
    "accepteren", "alles accepteren",
    "cookies accepteren", "ik ga akkoord",
    "akkoord", "toestaan", "sta toe",
    "toestaan cookies", "toestaan alles",

    # Polish
    "akceptuj", "zaakceptuj", "akceptuj wszystko",
    "akceptuj ciasteczka", "zgadzam sie",
    "zgoda", "pozwol", "pozwol ciasteczka",
    "zatwierdz",

    # Swedish
    "acceptera", "acceptera alla",
    "acceptera cookies", "godkänn",
    "jag godkänner", "tillåt",
    "tillåt alla", "tillåt cookies",
    "okej", "acceptera alltid"
]


def xpath_string_literal(s):
    """
    Erzeugt einen gültigen XPath-String,
    auch wenn Apostrophe enthalten sind.
    """
    if "'" not in s:
        return f"'{s}'"

    parts = s.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

def generate_xpaths():
    xpaths = []
    for word in KEYWORDS:
        safe_word = xpath_string_literal(word)
        xpath = (
            "//button[contains(translate(normalize-space(.), '{UPPER}', '{LOWER}'), {safe_word})]"
            " | //a[contains(translate(normalize-space(.), '{UPPER}', '{LOWER}'), {safe_word})]"
            " | //input[@type='button' or @type='submit'][contains(translate(@value, '{UPPER}', '{LOWER}'), {safe_word})]"
        ).format(UPPER=UPPER, LOWER=LOWER, safe_word=safe_word)
        # normalize whitespace (sicherstellen, dass keine unerwarteten Zeilenumbrüche/Tabulatoren bleiben)
        xpath = re.sub(r'\s+', ' ', xpath).strip()
        xpaths.append(xpath)
    return xpaths
