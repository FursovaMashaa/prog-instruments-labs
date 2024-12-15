import pytest

from unittest.mock import patch

from NIST_tests import frequency_bitwise_test, the_same_consecutive_bits, analyze_sequence


sequences = {
    "cpp": "00001010011101111001000110110111001011010101111101001110010010111110111111101111100101101111100011011000100011000011101110101100",
    "java": "11000011111110111101111111001010111101001001100010011011101110111010010000111110111101010001100110011000000011011000100101110111"
}

expected_results = {
    "cpp": {
        "frequency_bitwise_test": 0.07709987174354183,
        "the_same_consecutive_bits": 0.9368137041187848,
        "analyze_sequence": 0.718013202470707
    },
    "java": {
        "frequency_bitwise_test": 0.11161176829829222,
        "the_same_consecutive_bits": 0.39320937215824525,
        "analyze_sequence": 0.357873168545895
    }
}


def test_bit_frequency_cpp():
    frequency = expected_results["cpp"]["frequency_bitwise_test"]
    assert frequency_bitwise_test(sequences["cpp"]) == pytest.approx(frequency)


def test_consecutive_bit_test_cpp():
    frequency = expected_results["cpp"]["the_same_consecutive_bits"]
    assert the_same_consecutive_bits(
        sequences["cpp"]) == pytest.approx(frequency)


def test_longest_run_of_ones_test_cpp():
    frequency = expected_results["cpp"]["analyze_sequence"]
    assert analyze_sequence(sequences["cpp"]) == pytest.approx(frequency)


@pytest.mark.parametrize("lang, expected_value", [
    ("cpp", expected_results["cpp"]["frequency_bitwise_test"]),
])
@patch('NIST_tests.frequency_bitwise_test')
def test_frequency_bitwise_test_cpp(mock_frequency_bitwise_test, lang, expected_value):
    mock_frequency_bitwise_test.return_value = expected_value
    result = frequency_bitwise_test(sequences[lang])
    assert result == pytest.approx(expected_value)


@pytest.mark.parametrize("lang, expected_value", [
    ("java", expected_results["java"]["frequency_bitwise_test"]),
])
@patch('NIST_tests.frequency_bitwise_test')
def test_frequency_bitwise_test_java(mock_frequency_bitwise_test, lang, expected_value):
    mock_frequency_bitwise_test.return_value = expected_value
    result = frequency_bitwise_test(sequences[lang])
    assert result == pytest.approx(expected_value)


@pytest.mark.parametrize("lang, expected_value", [
    ("cpp", expected_results["cpp"]["the_same_consecutive_bits"]),
])
@patch('NIST_tests.the_same_consecutive_bits')
def test_the_same_consecutive_bits_cpp(mock_the_same_consecutive_bits, lang, expected_value):
    mock_the_same_consecutive_bits.return_value = expected_value
    result = the_same_consecutive_bits(sequences[lang])
    assert result == pytest.approx(expected_value)


@pytest.mark.parametrize("lang, expected_value", [
    ("java", expected_results["java"]["the_same_consecutive_bits"]),
])
@patch('NIST_tests.the_same_consecutive_bits')
def test_the_same_consecutive_bits_java(mock_the_same_consecutive_bits, lang, expected_value):
    mock_the_same_consecutive_bits.return_value = expected_value
    result = the_same_consecutive_bits(sequences[lang])
    assert result == pytest.approx(expected_value)


@pytest.mark.parametrize("lang, expected_value", [
    ("cpp", expected_results["cpp"]["analyze_sequence"]),
])
@patch('NIST_tests.analyze_sequence')
def test_analyze_sequence_cpp(mock_analyze_sequence, lang, expected_value):
    mock_analyze_sequence.return_value = expected_value
    result = analyze_sequence(sequences[lang])
    assert result == pytest.approx(expected_value)


@pytest.mark.parametrize("lang, expected_value", [
    ("java", expected_results["java"]["analyze_sequence"]),
])
@patch('NIST_tests.analyze_sequence')
def test_analyze_sequence_java(mock_analyze_sequence, lang, expected_value):
    mock_analyze_sequence.return_value = expected_value
    result = analyze_sequence(sequences[lang])
    assert result == pytest.approx(expected_value)
