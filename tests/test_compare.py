"""Unit tests for core/compare.py deterministic scientific comparator.

NOTE: Synthetic test fixtures live exclusively inside this test module.
"""
import pytest
from core.compare import compare_experiments

SYNTHETIC_EXP_A = {
    "staging_id": 1,
    "experiment_series": "SYNTH_SERIES_1",
    "fuel": "Heptane",
    "fuel_class": "droplet",
    "geometry": "spherical",
    "gravity_level": "microgravity",
    "flow_regime": "quiescent",
    "flow_velocity_cm_s": 0.0,
    "O2_value": 0.21,
    "O2_basis": "mole_fraction",
    "pressure_std_kPa": 101.3,
    "scale_dimension_raw": "d0 = 2.0 mm",
    "metric_name": "burning_rate_constant_K",
    "metric_value_std": 0.65,
    "metric_uncertainty_raw": 0.03,
    "metric_unit_std": "mm^2/s",
    "conversion_provenance": "Direct kPa",
    "source_paper": "Synthetic NASA Report 1",
    "source_page": 12,
    "curated_by": "Curator_A",
    "verified_by": "Verifier_B"
}

SYNTHETIC_EXP_B_MATCH = {
    "staging_id": 2,
    "experiment_series": "SYNTH_SERIES_2",
    "fuel": "Heptane",
    "fuel_class": "droplet",
    "geometry": "spherical",
    "gravity_level": "microgravity",
    "flow_regime": "quiescent",
    "flow_velocity_cm_s": 0.0,
    "O2_value": 0.21,
    "O2_basis": "mole_fraction",
    "pressure_std_kPa": 101.3,
    "scale_dimension_raw": "d0 = 2.0 mm",
    "metric_name": "burning_rate_constant_K",
    "metric_value_std": 0.62,
    "metric_uncertainty_raw": 0.04,
    "metric_unit_std": "mm^2/s",
    "conversion_provenance": "Direct kPa",
    "source_paper": "Synthetic NASA Report 2",
    "source_page": 8,
    "curated_by": "Curator_A",
    "verified_by": "Verifier_B"
}

SYNTHETIC_EXP_C_MISMATCH_GEOM = {
    "staging_id": 3,
    "experiment_series": "SYNTH_SERIES_3",
    "fuel": "PMMA",
    "fuel_class": "cast_solid",
    "geometry": "flat_slab",
    "gravity_level": "microgravity",
    "flow_regime": "forced_laminar",
    "flow_velocity_cm_s": 15.0,
    "O2_value": 0.21,
    "O2_basis": "mole_fraction",
    "pressure_std_kPa": 101.3,
    "scale_dimension_raw": "10 cm slab",
    "metric_name": "burning_rate_constant_K",
    "metric_value_std": 1.2,
    "metric_uncertainty_raw": None,
    "conversion_provenance": "Direct kPa",
    "source_paper": "Synthetic Solid Report",
    "source_page": 4,
    "curated_by": "Curator_A",
    "verified_by": "Verifier_B"
}


def test_compare_matching_experiments():
    res = compare_experiments(SYNTHETIC_EXP_A, SYNTHETIC_EXP_B_MATCH)
    assert res["state"] == "PASS"
    assert res["uncertainty_reported"] is True
    assert res["value_a"] == 0.65
    assert res["value_b"] == 0.62
    assert all(c["result"] == "pass" for c in res["checks"])


def test_compare_guardrail_failure_fuel_geometry():
    res = compare_experiments(SYNTHETIC_EXP_A, SYNTHETIC_EXP_C_MISMATCH_GEOM)
    assert res["state"] == "GUARDRAIL_FAILURE"
    
    geom_check = next(c for c in res["checks"] if c["name"] == "Fuel Class & Geometry")
    assert geom_check["result"] == "failure"
    assert "incompatible regimes" in geom_check["reason"].lower()


def test_compare_guardrail_failure_flow_regime():
    exp_forced = dict(SYNTHETIC_EXP_A)
    exp_forced["flow_regime"] = "forced_laminar"
    exp_forced["flow_velocity_cm_s"] = 10.0
    
    res = compare_experiments(SYNTHETIC_EXP_A, exp_forced)
    assert res["state"] == "GUARDRAIL_FAILURE"
    
    flow_check = next(c for c in res["checks"] if c["name"] == "Flow & Convection Regime")
    assert flow_check["result"] == "failure"
    assert "Convective regime mismatch" in flow_check["reason"]


def test_compare_guardrail_failure_gravity_level():
    exp_1g = dict(SYNTHETIC_EXP_A)
    exp_1g["gravity_level"] = "normal_1g"
    
    res = compare_experiments(SYNTHETIC_EXP_A, exp_1g)
    assert res["state"] == "GUARDRAIL_FAILURE"
    
    grav_check = next(c for c in res["checks"] if c["name"] == "Gravitational Acceleration Level")
    assert grav_check["result"] == "failure"
    assert "Gravity level mismatch" in grav_check["reason"]


def test_compare_guardrail_failure_metric_name():
    exp_diff_metric = dict(SYNTHETIC_EXP_A)
    exp_diff_metric["metric_name"] = "flame_spread_rate"
    
    res = compare_experiments(SYNTHETIC_EXP_A, exp_diff_metric)
    assert res["state"] == "GUARDRAIL_FAILURE"
    
    m_check = next(c for c in res["checks"] if c["name"] == "Physical Metric Compatibility")
    assert m_check["result"] == "failure"
    assert "Disparate physical metrics" in m_check["reason"]


def test_compare_guardrail_failure_unverified_pressure():
    exp_unverified_p = dict(SYNTHETIC_EXP_A)
    exp_unverified_p["pressure_std_kPa"] = None
    exp_unverified_p["conversion_provenance"] = None
    
    res = compare_experiments(SYNTHETIC_EXP_A, exp_unverified_p)
    assert res["state"] == "GUARDRAIL_FAILURE"
    
    p_check = next(c for c in res["checks"] if c["name"] == "Ambient Pressure")
    assert p_check["result"] == "failure"
    assert "missing" in p_check["reason"].lower()


def test_compare_warning_pressure_mismatch():
    exp_low_p = dict(SYNTHETIC_EXP_A)
    exp_low_p["pressure_std_kPa"] = 50.0  # Big pressure difference
    
    res = compare_experiments(SYNTHETIC_EXP_A, exp_low_p)
    assert res["state"] == "PASS_WITH_WARNINGS"
    
    p_check = next(c for c in res["checks"] if c["name"] == "Ambient Pressure")
    assert p_check["result"] == "warning"
    assert "exceeds 10% tolerance" in p_check["reason"]
