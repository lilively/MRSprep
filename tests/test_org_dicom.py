#from Organization.org_dicom import get_echo_suffix, determine_file_type, get_echo_time

# def test_short_echo_is_SE():
#     assert get_echo_suffix(30) == "SE"

# def test_long_echo_is_LE():
#     assert get_echo_suffix(136) == "LE"

# def test_echo_is_None():
#     assert get_echo_suffix(None) == "XX"

import pytest
from Organization.org_dicom import get_echo_suffix, determine_file_type

@pytest.mark.parametrize("echo_time, expected", [
    (30, "SE"),     # short echo
    (136, "LE"),    # long echo
    (50, "LE"),     # boundary
    (None, "XX"),   # missing
])

def test_get_echo_suffix(echo_time, expected):
    assert get_echo_suffix(echo_time) == expected

def make_attrs(**changes):
    attrs = {"pulse_sequence_name": "", "acquisition_contrast": "",
             "image_type": "", "series_description": "", "protocol_name": ""}
    attrs.update(changes)
    return attrs

def test_mrs_without_protocol_gives_error():
    attrs = make_attrs(pulse_sequence_name="SPECTROSCOPY",
                       acquisition_contrast="SPECTROSCOPY")
    file_type, error = determine_file_type(attrs)
    assert file_type == "Spectroscopy"
    assert error is not None

def test_unknown_file_type():
    file_type, error = determine_file_type(make_attrs())
    assert file_type == "Unknown"

def test_mrs_t1_image_detected():
    attrs = make_attrs(series_description="T1",
                       image_type ="T1")
    file_type, error = determine_file_type(attrs)
    assert file_type == "T1-weighted Image"
    assert error is None

