"""CombustionLens Core: Deterministic Unit Conversion and Standardization.

HARD RULE: Unknown or unsupported units raise ValueError. Never guess.
Every conversion returns (standardized_value, standardized_unit, provenance_string).
"""
import re
from typing import Tuple, Optional


def _matches_token(token: str, text: str) -> bool:
    """Matches token using word/underscore boundaries to prevent collisions like 'loc' in 'velocity'."""
    pattern = rf"(?:\b|_){re.escape(token)}(?:\b|_)"
    return bool(re.search(pattern, text))



def convert_pressure_to_kpa(value: Optional[float], unit: Optional[str]) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """Convert pressure to standard kPa.
    
    Supported units: 'kpa', 'atm', 'bar', 'torr'.
    Returns: (value_kpa, 'kPa', provenance)
    """
    if value is None or unit is None:
        return None, None, None
        
    u = unit.strip().lower()
    
    if u == "kpa":
        return round(float(value), 4), "kPa", "Direct value (reported in kPa)"
    elif u == "atm":
        # 1 atm = 101.325 kPa exact standard
        val_kpa = float(value) * 101.325
        return round(val_kpa, 4), "kPa", f"Converted from atm: {value} atm * 101.325 kPa/atm"
    elif u == "bar":
        # 1 bar = 100.0 kPa exact standard
        val_kpa = float(value) * 100.0
        return round(val_kpa, 4), "kPa", f"Converted from bar: {value} bar * 100.0 kPa/bar"
    elif u == "torr":
        # 1 torr = 101.325 / 760 kPa ≈ 0.133322 kPa
        val_kpa = float(value) * (101.325 / 760.0)
        return round(val_kpa, 4), "kPa", f"Converted from torr: {value} torr * (101.325/760) kPa/torr"
    else:
        raise ValueError(f"Unknown or unsupported pressure unit: '{unit}'. Guessing prohibited.")


def harmonize_o2_basis(value: Optional[float], basis: Optional[str]) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """Harmonize oxygen concentration to standard mole fraction (0.0 to 1.0).
    
    Supported bases:
    - 'mole_fraction': direct (must be within [0.0, 1.0])
    - 'volume_percent': ideal gas assumption: value / 100.0
    - 'mass_fraction': requires mixture gas composition; unsupported without diluent MW
    """
    if value is None or basis is None:
        return None, None, None
        
    b = basis.strip().lower()
    
    if b == "mole_fraction":
        val = float(value)
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"Mole fraction must be between 0.0 and 1.0, got: {value}")
        return round(val, 6), "mole_fraction", "Direct mole fraction (as reported)"
    elif b == "volume_percent":
        val = float(value)
        if not (0.0 <= val <= 100.0):
            raise ValueError(f"Volume percent must be between 0.0 and 100.0, got: {value}")
        mole_frac = val / 100.0
        return round(mole_frac, 6), "mole_fraction", f"Converted from volume percent: {value}% / 100.0 (ideal gas)"
    elif b == "mass_fraction":
        raise ValueError("Cannot convert mass_fraction to mole_fraction without mixture molecular weights. Guessing prohibited.")
    else:
        raise ValueError(f"Unknown or unsupported O2 basis: '{basis}'. Guessing prohibited.")


def standardize_metric(metric_name: str, value: Optional[float], unit: Optional[str]) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """Standardize combustion metrics to standard SI units.
    
    Supported metrics & targets:
    - Burning rate constant (K): standard unit 'mm^2/s'
    - Flame spread rate / regression rate: standard unit 'mm/s'
    - Flame length / dimension: standard unit 'mm'
    """
    if value is None or unit is None:
        return None, None, None
        
    m_name = metric_name.strip().lower()
    u = unit.strip().lower().replace(" ", "")
    v = float(value)
    
    # Burning rate constant (K) -> mm^2/s
    if any(k in m_name for k in ["burning_rate", "burning_constant", "d2_law"]):
        if u in ["mm^2/s", "mm2/s"]:
            return round(v, 6), "mm^2/s", "Direct value (reported in mm^2/s)"
        elif u in ["cm^2/s", "cm2/s"]:
            # 1 cm^2/s = 100 mm^2/s
            return round(v * 100.0, 6), "mm^2/s", f"Converted from cm^2/s: {value} * 100.0"
        elif u in ["m^2/s", "m2/s"]:
            # 1 m^2/s = 1,000,000 mm^2/s
            return round(v * 1_000_000.0, 6), "mm^2/s", f"Converted from m^2/s: {value} * 10^6"
        else:
            raise ValueError(f"Unsupported unit '{unit}' for burning rate constant '{metric_name}'. Guessing prohibited.")
            
    # Flame spread rate / regression rate -> mm/s
    elif any(k in m_name for k in ["flame_spread", "spread_rate", "regression_rate"]):
        if u == "mm/s":
            return round(v, 6), "mm/s", "Direct value (reported in mm/s)"
        elif u == "cm/s":
            # 1 cm/s = 10 mm/s
            return round(v * 10.0, 6), "mm/s", f"Converted from cm/s: {value} * 10.0"
        elif u == "m/s":
            # 1 m/s = 1000 mm/s
            return round(v * 1000.0, 6), "mm/s", f"Converted from m/s: {value} * 1000.0"
        else:
            raise ValueError(f"Unsupported unit '{unit}' for spread rate '{metric_name}'. Guessing prohibited.")
            
    # Length / Dimension -> mm
    elif any(k in m_name for k in ["length", "width", "diameter", "dimension", "standoff"]):
        if u == "mm":
            return round(v, 6), "mm", "Direct value (reported in mm)"
        elif u == "cm":
            return round(v * 10.0, 6), "mm", f"Converted from cm: {value} * 10.0"
        elif u == "m":
            return round(v * 1000.0, 6), "mm", f"Converted from m: {value} * 1000.0"
        else:
            raise ValueError(f"Unsupported unit '{unit}' for dimension '{metric_name}'. Guessing prohibited.")

    # Burn duration / extinction time / ignition delay -> s
    elif any(k in m_name for k in ["duration", "extinction_time", "burn_time", "ignition_delay", "delay"]):
        if u in ["s", "sec", "seconds"]:
            return round(v, 6), "s", "Direct value (reported in seconds)"
        elif u in ["ms", "msec", "milliseconds"]:
            return round(v / 1000.0, 6), "s", f"Converted from ms: {value} / 1000.0"
        elif u in ["min", "minute", "minutes"]:
            return round(v * 60.0, 6), "s", f"Converted from min: {value} * 60.0"
        else:
            raise ValueError(f"Unsupported unit '{unit}' for duration '{metric_name}'. Guessing prohibited.")

    # Extinction limit / limiting oxygen concentration (LOC/LOI) -> % or mole_fraction
    elif any(_matches_token(k, m_name) for k in ["extinction_limit", "limiting_oxygen", "loc", "loi", "mcor"]):
        if u in ["%", "vol%", "volume_percent", "vol_percent"]:
            return round(v, 6), "%", "Direct value (reported in volume %)"
        elif u == "mole_fraction":
            return round(v, 6), "mole_fraction", "Direct value (reported in mole fraction)"
        else:
            raise ValueError(f"Unsupported unit '{unit}' for extinction limit '{metric_name}'. Guessing prohibited.")

    else:
        # If metric name is unknown, we cannot safely guess target unit!
        raise ValueError(f"Unknown metric category: '{metric_name}'. Cannot standardize without physical definition.")
