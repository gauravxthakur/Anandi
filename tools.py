from langchain_core.tools import tool
from rag.hadlock_lookup import calculate_gestational_age, hadlock
from typing import Optional, Dict, Any


@tool
def fetal_biometry_calculator(bpd_mm: Optional[float] = None, 
                              hc_mm: Optional[float] = None, 
                              ac_mm: Optional[float] = None, 
                              fl_mm: Optional[float] = None,
                              gestational_weeks: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate fetal biometry relationships - measurements to gestational age or vice versa.
    
    Given measurements: calculates gestational age using Hadlock reference data.
    Given gestational age: returns expected measurements from reference data.
    Given both: compares measurements against expected for validation.
    
    Args:
        bpd_mm: Biparietal diameter in millimeters
        hc_mm: Head circumference in millimeters  
        ac_mm: Abdominal circumference in millimeters
        fl_mm: Femur length in millimeters
        gestational_weeks: Expected gestational age in weeks (for reverse lookup/validation)
    
    Returns:
        Dictionary with calculated gestational ages, expected measurements, or comparison results.
    """
    # If measurements provided, calculate gestational age
    if any([bpd_mm, hc_mm, ac_mm, fl_mm]):
        calculated_ages = calculate_gestational_age(bpd_mm, hc_mm, ac_mm, fl_mm)
        
        # If also provided gestational weeks, do comparison
        if gestational_weeks:
            discrepancies = {}
            for measurement, calculated_weeks in calculated_ages.items():
                if calculated_weeks is not None:
                    diff = calculated_weeks - gestational_weeks
                    discrepancies[measurement] = {
                        "calculated_weeks": calculated_weeks,
                        "difference_weeks": diff,
                        "within_normal_range": abs(diff) <= 2.0
                    }
            
            return {
                "calculated_ages": calculated_ages,
                "expected_weeks": gestational_weeks,
                "comparison": discrepancies
            }
        
        return {"calculated_gestational_ages": calculated_ages}
    
    # If only gestational weeks provided, return expected measurements
    elif gestational_weeks:
        # Find nearest reference point
        data_points = hadlock.get_reference_data()['data']
        nearest = min(data_points, key=lambda x: abs(x['gestational_age_weeks'] - gestational_weeks))
        
        return {
            "expected_measurements_for_weeks": gestational_weeks,
            "nearest_reference_week": nearest['gestational_age_weeks'],
            "expected_bpd_mm": nearest['bpd_mean'],
            "expected_hc_mm": nearest['hc_mean'],
            "expected_ac_mm": nearest['ac_mean'],
            "expected_fl_mm": nearest['fl_mean']
        }
    
    else:
        return {"error": "Provide either measurements or gestational_weeks"}