from ..automation.Commands.utils.webdriver_utils import parse_neterror


def test_parse_neterror():
    text = "selenium.common.exceptions.WebDriverException: "
    "Message: Reached error page: "
    "about:neterror?e=dnsNotFound&u=http%3A//medmood.it/&c=UTF-8&"
    "f=regular&d=We%20can%E2%80%99t%20"
    "connect%20to%20the%20server%20at%20medmood.it."
    assert parse_neterror(text) == "dnsNotFound"
