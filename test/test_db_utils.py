from typing import Optional

import pytest

from openwpm.utilities.db_utils import legacy_symbol

pytestmark = pytest.mark.pyonly


@pytest.mark.parametrize(
    "symbol,receiver,expected",
    [
        ("AudioNode.connect", "GainNode", "GainNode.connect"),
        (
            "[AudioContext|OfflineAudioContext].createGain",
            "OfflineAudioContext",
            "OfflineAudioContext.createGain",
        ),
        (
            "EventTarget.addEventListener",
            "HTMLDivElement",
            "HTMLDivElement.addEventListener",
        ),
        # Owner is the receiver's own interface.
        ("GainNode.gain", "GainNode", "GainNode.gain"),
        # Legacy rows.
        ("GainNode.connect", None, "GainNode.connect"),
        # Instance paths.
        ("window.document.cookie", "HTMLDocument", "window.document.cookie"),
        ("window.name", "Window", "window.name"),
        ("window.navigator.userAgent", "Navigator", "window.navigator.userAgent"),
        # Not an interface label.
        ("[audioContext].createGain", "AudioContext", "[audioContext].createGain"),
        ("[AudioContext|].createGain", "AudioContext", "[AudioContext|].createGain"),
        ("connect", "GainNode", "connect"),
    ],
)
def test_legacy_symbol(symbol: str, receiver: Optional[str], expected: str) -> None:
    assert legacy_symbol(symbol, receiver) == expected
