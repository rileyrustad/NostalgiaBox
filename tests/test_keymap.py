import pytest

from nostalgiabox.actions import Action
from nostalgiabox.input.keymap import (
    cec_key_to_event,
    evdev_key_to_event,
    parse_key_overrides,
    stdin_char_to_event,
    stdin_escape_to_event,
)


def test_evdev_channel_and_volume():
    assert evdev_key_to_event("KEY_CHANNELUP").action == Action.CHANNEL_UP
    assert evdev_key_to_event("KEY_PAGEUP").action == Action.CHANNEL_UP
    assert evdev_key_to_event("KEY_UP").action == Action.CHANNEL_UP
    assert evdev_key_to_event("KEY_VOLUMEDOWN").action == Action.VOLUME_DOWN
    assert evdev_key_to_event("KEY_MUTE").action == Action.MUTE


def test_evdev_digits():
    ev = evdev_key_to_event("KEY_5")
    assert ev.action == Action.DIGIT and ev.value == 5
    ev = evdev_key_to_event("KEY_KP0")
    assert ev.action == Action.DIGIT and ev.value == 0


def test_evdev_power_and_last_letters():
    assert evdev_key_to_event("KEY_P").action == Action.POWER
    assert evdev_key_to_event("KEY_L").action == Action.LAST_CHANNEL
    assert evdev_key_to_event("KEY_POWER").action == Action.POWER


def test_evdev_unknown_key():
    assert evdev_key_to_event("KEY_FLIBBERTIGIBBET") is None


def test_stdin_chars():
    assert stdin_char_to_event("+").action == Action.VOLUME_UP
    assert stdin_char_to_event("-").action == Action.VOLUME_DOWN
    assert stdin_char_to_event("m").action == Action.MUTE
    assert stdin_char_to_event("q").action == Action.QUIT
    assert stdin_char_to_event("3").value == 3
    assert stdin_char_to_event("\r").action == Action.ENTER


def test_stdin_arrows():
    assert stdin_escape_to_event("[A").action == Action.CHANNEL_UP
    assert stdin_escape_to_event("[B").action == Action.CHANNEL_DOWN
    assert stdin_escape_to_event("[C").action == Action.VOLUME_UP
    assert stdin_escape_to_event("[D").action == Action.VOLUME_DOWN
    assert stdin_escape_to_event("[Z") is None


def test_parse_key_overrides_basic():
    ov = parse_key_overrides({"KEY_F5": "volume_up", "KEY_DOT": "volume_down"})
    assert ov["KEY_F5"].action == Action.VOLUME_UP
    assert ov["KEY_DOT"].action == Action.VOLUME_DOWN


def test_parse_key_overrides_normalises_names():
    # bare names get the KEY_ prefix and are upper-cased
    ov = parse_key_overrides({"f5": "channel_up", "pageup": "channel_down"})
    assert ov["KEY_F5"].action == Action.CHANNEL_UP
    assert ov["KEY_PAGEUP"].action == Action.CHANNEL_DOWN


def test_parse_key_overrides_digit_and_none():
    ov = parse_key_overrides({"KEY_KP5": "digit_5", "KEY_ESC": "none"})
    assert ov["KEY_KP5"].value == 5
    assert ov["KEY_ESC"] is None  # explicitly unbound


def test_parse_key_overrides_rejects_bad_action():
    with pytest.raises(ValueError, match="unknown action"):
        parse_key_overrides({"KEY_F5": "explode"})


def test_parse_key_overrides_empty():
    assert parse_key_overrides(None) == {}
    assert parse_key_overrides({}) == {}


def test_keyboard_backend_override_precedence():
    from nostalgiabox.input.keyboard import KeyboardBackend

    ov = parse_key_overrides({"KEY_F5": "volume_up", "KEY_ESC": "none"})
    kb = KeyboardBackend(overrides=ov)
    assert kb._lookup("KEY_F5").action == Action.VOLUME_UP     # override applied
    assert kb._lookup("KEY_ESC") is None                       # explicitly unbound
    assert kb._lookup("KEY_VOLUMEUP").action == Action.VOLUME_UP  # default intact
    assert kb._lookup("KEY_PAGEUP").action == Action.CHANNEL_UP


def test_evdev_guide_nav_keys():
    assert evdev_key_to_event("KEY_W").action == Action.NAV_UP
    assert evdev_key_to_event("KEY_A").action == Action.NAV_LEFT
    assert evdev_key_to_event("KEY_S").action == Action.NAV_DOWN
    assert evdev_key_to_event("KEY_D").action == Action.NAV_RIGHT
    assert evdev_key_to_event("KEY_B").action == Action.BACK
    assert evdev_key_to_event("KEY_H").action == Action.HOME


def test_stdin_guide_nav_chars():
    assert stdin_char_to_event("w").action == Action.NAV_UP
    assert stdin_char_to_event("a").action == Action.NAV_LEFT
    assert stdin_char_to_event("s").action == Action.NAV_DOWN
    assert stdin_char_to_event("d").action == Action.NAV_RIGHT
    assert stdin_char_to_event("b").action == Action.BACK
    assert stdin_char_to_event("h").action == Action.HOME


def test_parse_key_overrides_guide_nav_action():
    ov = parse_key_overrides({"KEY_F5": "nav_up"})
    assert ov["KEY_F5"].action == Action.NAV_UP


def test_cec_keys():
    assert cec_key_to_event("channel up").action == Action.CHANNEL_UP
    assert cec_key_to_event("Volume Down").action == Action.VOLUME_DOWN
    assert cec_key_to_event("select").action == Action.ENTER
    assert cec_key_to_event("number 4").value == 4
    assert cec_key_to_event("power").action == Action.POWER
    assert cec_key_to_event("nonsense") is None
