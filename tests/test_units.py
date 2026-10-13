"""Unit tests for core/units.py deterministic conversions.

NOTE: Synthetic test fixtures live exclusively inside this test module.
"""
import pytest
from core.units import (
    convert_pressure_to_kpa,
    harmonize_o2_basis,
    standardize_metric,
)


def test_pressure_conversion_valid():
    # kPa (1:1)
    val, unit, prov = convert_pressure_to_kpa(101.3, "kPa")
    assert val == 101.3
    assert unit == "kPa"
    assert "Direct" in prov

    # atm -> kPa
    val, unit, prov = convert_pressure_to_kpa(1.0, "atm")
    assert val == 101.325
    assert unit == "kPa"
    assert "101.325" in prov

    # bar -> kPa
    val, unit, prov = convert_pressure_to_kpa(2.0, "bar")
    assert val == 200.0
    assert unit == "kPa"
    assert "100.0" in prov

    # torr -> kPa
    val, unit, prov = convert_pressure_to_kpa(760.0, "torr")
    assert abs(val - 101.325) < 0.001
    assert unit == "kPa"
    assert "torr" in prov


def test_pressure_conversion_unknown():
    with pytest.raises(ValueError, match="Unknown or unsupported pressure unit"):
        convert_pressure_to_kpa(14.7, "psi")


def test_pressure_conversion_none():
    val, unit, prov = convert_pressure_to_kpa(None, "kPa")
    assert val is None
    assert unit is None
    assert prov is None


def test_o2_basis_harmonization_valid():
    # mole_fraction direct
    val, basis, prov = harmonize_o2_basis(0.21, "mole_fraction")
    assert val == 0.21
    assert basis == "mole_fraction"
    assert "Direct" in prov

    # volume_percent -> mole_fraction
    val, basis, prov = harmonize_o2_basis(21.0, "volume_percent")
    assert val == 0.21
    assert basis == "mole_fraction"
    assert "100.0" in prov


def test_o2_basis_harmonization_invalid():
    # Mass fraction unsupported without mixture MW
    with pytest.raises(ValueError, match="Cannot convert mass_fraction"):
        harmonize_o2_basis(0.23, "mass_fraction")

    # Unknown basis
    with pytest.raises(ValueError, match="Unknown or unsupported O2 basis"):
        harmonize_o2_basis(21.0, "ppm")

    # Out of range
    with pytest.raises(ValueError, match="Mole fraction must be between 0.0 and 1.0"):
        harmonize_o2_basis(1.5, "mole_fraction")

    with pytest.raises(ValueError, match="Volume percent must be between 0.0 and 100.0"):
        harmonize_o2_basis(120.0, "volume_percent")


def test_standardize_metric_burning_rate():
    # mm^2/s direct
    val, unit, prov = standardize_metric("burning_rate_constant_K", 0.65, "mm^2/s")
    assert val == 0.65
    assert unit == "mm^2/s"

    # cm^2/s -> mm^2/s
    val, unit, prov = standardize_metric("burning_rate_constant_K", 0.01, "cm^2/s")
    assert val == 1.0
    assert unit == "mm^2/s"


def test_standardize_metric_spread_rate():
    # cm/s -> mm/s
    val, unit, prov = standardize_metric("flame_spread_rate", 2.5, "cm/s")
    assert val == 25.0
    assert unit == "mm/s"


def test_standardize_metric_length():
    # cm -> mm
    val, unit, prov = standardize_metric("flame_length", 3.0, "cm")
    assert val == 30.0
    assert unit == "mm"


def test_standardize_metric_unknown():
    with pytest.raises(ValueError, match="Unknown metric category"):
        standardize_metric("unrecognized_property_xyz", 10.0, "mm")

    with pytest.raises(ValueError, match="Unsupported unit"):
        standardize_metric("burning_rate_constant_K", 10.0, "inches/hr")
