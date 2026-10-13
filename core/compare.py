"""CombustionLens Core: Deterministic Scientific Experiment Comparator.

Operates strictly over human-verified DuckDB experiments.
Evaluates physical compatibility in strict order:
1. Metric name match -> else GUARDRAIL FAILURE (Change Log Trigger 1)
2. Gravity level match -> else GUARDRAIL FAILURE (Change Log Trigger 1)
3. Fuel class and geometry match -> else GUARDRAIL FAILURE
4. Flow regime match (quiescent vs forced) -> missing = WARNING, mismatch = GUARDRAIL FAILURE
5. Oxygen basis harmonization & level compatibility -> standardized to mole fraction; mismatch = WARNING
6. Pressure standardized to kPa with verified provenance -> unverified/missing = GUARDRAIL FAILURE, >10% = WARNING
7. Scale / thickness disparities -> missing/mismatch = WARNING
8. Uncertainty error bars -> standardized with identical scaling factor as metric value

States: PASS | PASS_WITH_WARNINGS | GUARDRAIL_FAILURE
HARD RULE: Zero numbers fabricated. LLMs never touch or alter values.
"""
from typing import Dict, Any, List, Tuple, Optional
from core.units import harmonize_o2_basis


def scale_uncertainty(raw_val: Optional[float], std_val: Optional[float], raw_unc: Optional[float]) -> Optional[float]:
    """Scale metric uncertainty using the identical conversion ratio applied to the metric value."""
    if raw_unc is None:
        return None
    try:
        r_unc = float(raw_unc)
        if raw_val is not None and std_val is not None:
            r_val = float(raw_val)
            s_val = float(std_val)
            if r_val != 0:
                ratio = abs(s_val / r_val)
                return round(r_unc * ratio, 6)
        return round(r_unc, 6)
    except (ValueError, TypeError):
        return None


def compare_experiments(exp_a: Dict[str, Any], exp_b: Dict[str, Any]) -> Dict[str, Any]:
    """Execute deterministic scientific comparability checks between two verified experiments."""
    checks = []
    has_failure = False
    has_warning = False
    
    # 1. Metric Name Compatibility Check (Section 0 Plan Extension)
    m_name_a = str(exp_a.get("metric_name", "")).strip().lower()
    m_name_b = str(exp_b.get("metric_name", "")).strip().lower()
    if not m_name_a or not m_name_b or m_name_a != m_name_b:
        has_failure = True
        checks.append({
            "name": "Physical Metric Compatibility",
            "result": "failure",
            "reason": (
                f"Disparate physical metrics: Experiment A measures '{m_name_a or 'unspecified'}' "
                f"while Experiment B measures '{m_name_b or 'unspecified'}'. Direct quantitative comparison is invalid."
            ),
            "values": {"exp_a": m_name_a or "unspecified", "exp_b": m_name_b or "unspecified"}
        })
    else:
        checks.append({
            "name": "Physical Metric Compatibility",
            "result": "pass",
            "reason": f"Both experiments report the identical physical metric ('{m_name_a}').",
            "values": {"exp_a": m_name_a, "exp_b": m_name_b}
        })

    # 2. Gravity Level Compatibility Check (Section 0 Plan Extension)
    grav_a = str(exp_a.get("gravity_level", "")).strip().lower()
    grav_b = str(exp_b.get("gravity_level", "")).strip().lower()
    if not grav_a or not grav_b or grav_a != grav_b:
        has_failure = True
        checks.append({
            "name": "Gravitational Acceleration Level",
            "result": "failure",
            "reason": (
                f"Gravity level mismatch: Experiment A operates at '{grav_a or 'unspecified'}' "
                f"while Experiment B operates at '{grav_b or 'unspecified'}'. Buoyant acceleration fundamentally alters combustion regimes."
            ),
            "values": {"exp_a": grav_a or "unspecified", "exp_b": grav_b or "unspecified"}
        })
    else:
        checks.append({
            "name": "Gravitational Acceleration Level",
            "result": "pass",
            "reason": f"Both experiments operate under matching gravity regimes ('{grav_a}').",
            "values": {"exp_a": grav_a, "exp_b": grav_b}
        })

    # 3. Fuel Class & Geometry Match
    fc_a = str(exp_a.get("fuel_class", "")).strip().lower()
    fc_b = str(exp_b.get("fuel_class", "")).strip().lower()
    geom_a = str(exp_a.get("geometry", "")).strip().lower()
    geom_b = str(exp_b.get("geometry", "")).strip().lower()
    
    if fc_a and fc_b and geom_a and geom_b and fc_a == fc_b and geom_a == geom_b:
        checks.append({
            "name": "Fuel Class & Geometry",
            "result": "pass",
            "reason": f"Both experiments share matching fuel class ('{fc_a}') and geometry ('{geom_a}').",
            "values": {"exp_a": f"{fc_a} / {geom_a}", "exp_b": f"{fc_b} / {geom_b}"}
        })
    else:
        has_failure = True
        checks.append({
            "name": "Fuel Class & Geometry",
            "result": "failure",
            "reason": (
                f"Incompatible regimes: Experiment A is '{fc_a or 'unspecified'}' ({geom_a or 'unspecified'}) "
                f"while Experiment B is '{fc_b or 'unspecified'}' ({geom_b or 'unspecified'}). Direct comparison would be unphysical."
            ),
            "values": {"exp_a": f"{fc_a or 'unspecified'} / {geom_a or 'unspecified'}", "exp_b": f"{fc_b or 'unspecified'} / {geom_b or 'unspecified'}"}
        })

    # 4. Flow Regime (Quiescent vs Forced)
    flow_a = str(exp_a.get("flow_regime", "")).strip().lower()
    flow_b = str(exp_b.get("flow_regime", "")).strip().lower()
    
    if not flow_a or not flow_b:
        has_warning = True
        checks.append({
            "name": "Flow & Convection Regime",
            "result": "warning",
            "reason": "Flow regime is unverified or missing for one or both experiments; convection comparability cannot be confirmed.",
            "values": {"exp_a": flow_a or "unverified", "exp_b": flow_b or "unverified"}
        })
    else:
        is_q_a = "quiescent" in flow_a
        is_q_b = "quiescent" in flow_b
        if is_q_a == is_q_b:
            regime_label = "quiescent" if is_q_a else "forced flow"
            checks.append({
                "name": "Flow & Convection Regime",
                "result": "pass",
                "reason": f"Both experiments operate under comparable convective regimes ({regime_label}: '{flow_a}' vs '{flow_b}').",
                "values": {"exp_a": flow_a, "exp_b": flow_b}
            })
        else:
            has_failure = True
            checks.append({
                "name": "Flow & Convection Regime",
                "result": "failure",
                "reason": (
                    f"Convective regime mismatch: Experiment A is '{flow_a}' while Experiment B is '{flow_b}'. "
                    "Quiescent microgravity combustion physics cannot be directly compared to forced convective flow."
                ),
                "values": {"exp_a": flow_a, "exp_b": flow_b}
            })

    # 5. Oxygen Equivalence (Standardized to Mole Fraction)
    o2_val_a = exp_a.get("O2_value")
    o2_val_b = exp_b.get("O2_value")
    basis_a = exp_a.get("O2_basis")
    basis_b = exp_b.get("O2_basis")
    
    std_o2_a, std_o2_b = None, None
    if o2_val_a is not None and basis_a:
        try:
            std_o2_a, _, _ = harmonize_o2_basis(float(o2_val_a), basis_a)
        except Exception:
            std_o2_a = None
    if o2_val_b is not None and basis_b:
        try:
            std_o2_b, _, _ = harmonize_o2_basis(float(o2_val_b), basis_b)
        except Exception:
            std_o2_b = None

    if std_o2_a is not None and std_o2_b is not None:
        diff_o2 = abs(std_o2_a - std_o2_b)
        # Tolerance threshold: 0.01 mole fraction (1.0% O2 equivalent)
        if diff_o2 <= 0.01:
            checks.append({
                "name": "Oxygen Concentration (Mole Fraction)",
                "result": "pass",
                "reason": f"Standardized oxygen concentrations match closely (divergence: {diff_o2:.4f} mole fraction).",
                "values": {"exp_a": f"{std_o2_a:.4f} ({basis_a})", "exp_b": f"{std_o2_b:.4f} ({basis_b})"}
            })
        else:
            has_warning = True
            checks.append({
                "name": "Oxygen Concentration (Mole Fraction)",
                "result": "warning",
                "reason": (
                    f"Atmospheric oxygen mismatch: Divergence of {diff_o2*100:.2f}% mole fraction observed. "
                    "(Note: comparison threshold is heuristic; empirical spacecraft flammability boundaries depend on fuel chemistry)."
                ),
                "values": {"exp_a": f"{std_o2_a:.4f} ({basis_a})", "exp_b": f"{std_o2_b:.4f} ({basis_b})"}
            })
    else:
        has_warning = True
        checks.append({
            "name": "Oxygen Concentration (Mole Fraction)",
            "result": "warning",
            "reason": "Oxygen concentration or basis is missing/unconvertible for one or both experiments.",
            "values": {"exp_a": f"{o2_val_a} ({basis_a})", "exp_b": f"{o2_val_b} ({basis_b})"}
        })

    # 6. Pressure Equivalence (Standardized to kPa)
    p_a = exp_a.get("pressure_std_kPa")
    p_b = exp_b.get("pressure_std_kPa")
    prov_a = exp_a.get("conversion_provenance")
    prov_b = exp_b.get("conversion_provenance")
    
    if p_a is None or p_b is None or not prov_a or not prov_b:
        # HARD RULE: Unverified standardized pressure is a GUARDRAIL FAILURE
        has_failure = True
        checks.append({
            "name": "Ambient Pressure",
            "result": "failure",
            "reason": "Standardized pressure in kPa or verified conversion provenance is missing. Direct comparison is prohibited.",
            "values": {"exp_a": f"{p_a} kPa" if p_a is not None else "not verified", "exp_b": f"{p_b} kPa" if p_b is not None else "not verified"}
        })
    else:
        avg_p = (float(p_a) + float(p_b)) / 2.0
        rel_diff = abs(float(p_a) - float(p_b)) / avg_p if avg_p > 0 else 0
        if rel_diff <= 0.10:
            checks.append({
                "name": "Ambient Pressure",
                "result": "pass",
                "reason": f"Standardized pressures match within 10% operational tolerance (diff: {rel_diff*100:.1f}%).",
                "values": {"exp_a": f"{p_a:.1f} kPa", "exp_b": f"{p_b:.1f} kPa"}
            })
        else:
            has_warning = True
            checks.append({
                "name": "Ambient Pressure",
                "result": "warning",
                "reason": (
                    f"Pressure divergence of {rel_diff*100:.1f}% exceeds 10% tolerance "
                    "(Note: 10% threshold is a rule-of-thumb; low-pressure hypoxic environments exhibit nonlinear extinction shifts)."
                ),
                "values": {"exp_a": f"{p_a:.1f} kPa", "exp_b": f"{p_b:.1f} kPa"}
            })

    # 7. Scale & Dimension
    scale_a = exp_a.get("scale_dimension_raw")
    scale_b = exp_b.get("scale_dimension_raw")
    if not scale_a or not scale_b:
        has_warning = True
        checks.append({
            "name": "Scale & Sample Dimension",
            "result": "warning",
            "reason": "Scale/dimension is unverified or missing for one or both samples.",
            "values": {"exp_a": scale_a or "unverified", "exp_b": scale_b or "unverified"}
        })
    elif scale_a != scale_b:
        has_warning = True
        checks.append({
            "name": "Scale & Sample Dimension",
            "result": "warning",
            "reason": f"Scale disparity noted between samples: '{scale_a}' vs '{scale_b}'.",
            "values": {"exp_a": scale_a, "exp_b": scale_b}
        })
    else:
        checks.append({
            "name": "Scale & Sample Dimension",
            "result": "pass",
            "reason": f"Sample scales are consistent ('{scale_a}').",
            "values": {"exp_a": scale_a, "exp_b": scale_b}
        })

    # Resolve effective metric value and unit (fallback to raw when std is None)
    val_a = exp_a.get("metric_value_std") if exp_a.get("metric_value_std") is not None else exp_a.get("metric_value_raw")
    val_b = exp_b.get("metric_value_std") if exp_b.get("metric_value_std") is not None else exp_b.get("metric_value_raw")
    unit_a = exp_a.get("metric_unit_std") or exp_a.get("metric_unit_raw")
    unit_b = exp_b.get("metric_unit_std") or exp_b.get("metric_unit_raw")

    # Metric unit equivalence check
    if unit_a and unit_b and unit_a != unit_b:
        has_failure = True
        checks.append({
            "name": "Physical Metric Units",
            "result": "failure",
            "reason": (
                f"Disparate metric units: Experiment A reports '{unit_a}' while Experiment B reports '{unit_b}'. "
                "Direct numeric comparison between unharmonized units is scientifically invalid."
            ),
            "values": {"exp_a": unit_a, "exp_b": unit_b}
        })

    # Diluent check
    dil_a = str(exp_a.get("diluent") or "").strip().lower()
    dil_b = str(exp_b.get("diluent") or "").strip().lower()
    if dil_a and dil_b and dil_a != dil_b:
        has_warning = True
        checks.append({
            "name": "Inert Diluent Equivalence",
            "result": "warning",
            "reason": (
                f"Inert diluent mismatch: Experiment A uses '{dil_a}' while Experiment B uses '{dil_b}'. "
                "Different molar heat capacities and mass diffusivities alter extinction and flame structure."
            ),
            "values": {"exp_a": dil_a, "exp_b": dil_b}
        })

    # 8. Uncertainty Error Bars (Proportionally Scaled to Standardized Units)
    unc_a_scaled = scale_uncertainty(exp_a.get("metric_value_raw"), exp_a.get("metric_value_std"), exp_a.get("metric_uncertainty_raw"))
    unc_b_scaled = scale_uncertainty(exp_b.get("metric_value_raw"), exp_b.get("metric_value_std"), exp_b.get("metric_uncertainty_raw"))
    uncertainty_reported = (unc_a_scaled is not None and unc_b_scaled is not None)
    
    # Determine overall state
    if has_failure:
        overall_state = "GUARDRAIL_FAILURE"
    elif has_warning:
        overall_state = "PASS_WITH_WARNINGS"
    else:
        overall_state = "PASS"

    return {
        "state": overall_state,
        "checks": checks,
        "series_a": exp_a.get("experiment_series", "Series A"),
        "series_b": exp_b.get("experiment_series", "Series B"),
        "metric_name": exp_a.get("metric_name") or exp_b.get("metric_name"),
        "metric_unit": unit_a if unit_a == unit_b else f"{unit_a} vs {unit_b}",
        "unit_a": unit_a,
        "unit_b": unit_b,
        "value_a": val_a,
        "value_b": val_b,
        "uncertainty_a": unc_a_scaled,
        "uncertainty_b": unc_b_scaled,
        "uncertainty_reported": uncertainty_reported,
        "provenance": {
            "exp_a": {
                "source_paper": exp_a.get("source_paper"),
                "source_page": exp_a.get("source_page"),
                "curated_by": exp_a.get("curated_by"),
                "verified_by": exp_a.get("verified_by"),
                "conversion_provenance": exp_a.get("conversion_provenance")
            },
            "exp_b": {
                "source_paper": exp_b.get("source_paper"),
                "source_page": exp_b.get("source_page"),
                "curated_by": exp_b.get("curated_by"),
                "verified_by": exp_b.get("verified_by"),
                "conversion_provenance": exp_b.get("conversion_provenance")
            }
        },
        "harmonized_units": {
            "pressure": "kPa",
            "oxygen": "mole_fraction"
        }
    }
