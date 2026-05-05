"""
Hadlock fetal biometry lookup module.

Provides structured access to Hadlock reference data for gestational age
estimation based on fetal measurements (BPD, HC, AC, FL).

This is used directly by the auditor workflow, NOT via vector search.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class HadlockLookup:
    """Hadlock reference data lookup with interpolation."""
    
    def __init__(self, json_path: str = "rag/data/hadlock.json"):
        """Load Hadlock reference data from JSON file."""
        self.json_path = Path(json_path)
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load and validate Hadlock data."""
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        # Sort data by gestational age for interpolation
        data['data'].sort(key=lambda x: x['gestational_age_weeks'])
        return data
    
    def _find_nearest_data_points(self, measurement_mm: float, 
                                 measurement_type: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Find two data points surrounding the measurement for interpolation."""
        data_points = self.data['data']
        
        lower = None
        upper = None
        
        for point in data_points:
            if point[f'{measurement_type}_mean'] <= measurement_mm:
                lower = point
            elif point[f'{measurement_type}_mean'] > measurement_mm and upper is None:
                upper = point
                break
        
        return lower, upper
    
    def _linear_interpolation(self, measurement_mm: float, 
                            lower_point: Dict, upper_point: Dict, 
                            measurement_type: str) -> float:
        """Linear interpolation between two data points."""
        lower_meas = lower_point[f'{measurement_type}_mean']
        upper_meas = upper_point[f'{measurement_type}_mean']
        lower_ga = lower_point['gestational_age_weeks']
        upper_ga = upper_point['gestational_age_weeks']
        
        # Linear interpolation formula
        ratio = (measurement_mm - lower_meas) / (upper_meas - lower_meas)
        interpolated_ga = lower_ga + ratio * (upper_ga - lower_ga)
        
        return interpolated_ga
    
    def ga_for_bpd(self, bpd_mm: float) -> Optional[float]:
        """Estimate gestational age from BPD measurement."""
        lower, upper = self._find_nearest_data_points(bpd_mm, 'bpd')
        
        if lower is None:
            return None  # Measurement below reference range
        elif upper is None:
            return lower['gestational_age_weeks']  # Measurement above reference range
        elif lower['bpd_mean'] == bpd_mm:
            return lower['gestational_age_weeks']  # Exact match
        else:
            return self._linear_interpolation(bpd_mm, lower, upper, 'bpd')
    
    def ga_for_hc(self, hc_mm: float) -> Optional[float]:
        """Estimate gestational age from HC measurement."""
        lower, upper = self._find_nearest_data_points(hc_mm, 'hc')
        
        if lower is None:
            return None
        elif upper is None:
            return lower['gestational_age_weeks']
        elif lower['hc_mean'] == hc_mm:
            return lower['gestational_age_weeks']
        else:
            return self._linear_interpolation(hc_mm, lower, upper, 'hc')
    
    def ga_for_ac(self, ac_mm: float) -> Optional[float]:
        """Estimate gestational age from AC measurement."""
        lower, upper = self._find_nearest_data_points(ac_mm, 'ac')
        
        if lower is None:
            return None
        elif upper is None:
            return lower['gestational_age_weeks']
        elif lower['ac_mean'] == ac_mm:
            return lower['gestational_age_weeks']
        else:
            return self._linear_interpolation(ac_mm, lower, upper, 'ac')
    
    def ga_for_fl(self, fl_mm: float) -> Optional[float]:
        """Estimate gestational age from FL measurement."""
        lower, upper = self._find_nearest_data_points(fl_mm, 'fl')
        
        if lower is None:
            return None
        elif upper is None:
            return lower['gestational_age_weeks']
        elif lower['fl_mean'] == fl_mm:
            return lower['gestational_age_weeks']
        else:
            return self._linear_interpolation(fl_mm, lower, upper, 'fl')
    
    def get_reference_data(self) -> Dict:
        """Get complete reference data."""
        return self.data
    
    def get_measurement_range(self, measurement_type: str) -> Tuple[float, float]:
        """Get min/max range for a measurement type."""
        data_points = self.data['data']
        values = [point[f'{measurement_type}_mean'] for point in data_points]
        return min(values), max(values)


# Global instance for easy access
hadlock = HadlockLookup()


# Convenience functions
def ga_for_bpd(bpd_mm: float) -> Optional[float]:
    """Convenience function: gestational age from BPD."""
    return hadlock.ga_for_bpd(bpd_mm)


def ga_for_hc(hc_mm: float) -> Optional[float]:
    """Convenience function: gestational age from HC."""
    return hadlock.ga_for_hc(hc_mm)


def ga_for_ac(ac_mm: float) -> Optional[float]:
    """Convenience function: gestational age from AC."""
    return hadlock.ga_for_ac(ac_mm)


def ga_for_fl(fl_mm: float) -> Optional[float]:
    """Convenience function: gestational age from FL."""
    return hadlock.ga_for_fl(fl_mm)


def calculate_gestational_age(bpd_mm: float = None, hc_mm: float = None, 
                              ac_mm: float = None, fl_mm: float = None) -> Dict[str, Optional[float]]:
    """
    Calculate gestational age from any combination of fetal measurements.
    
    Args:
        bpd_mm: Biparietal diameter in mm
        hc_mm: Head circumference in mm  
        ac_mm: Abdominal circumference in mm
        fl_mm: Femur length in mm
    
    Returns:
        Dictionary with gestational age estimates for each provided measurement
    """
    results = {}
    
    if bpd_mm is not None:
        results['bpd_weeks'] = hadlock.ga_for_bpd(bpd_mm)
    if hc_mm is not None:
        results['hc_weeks'] = hadlock.ga_for_hc(hc_mm)
    if ac_mm is not None:
        results['ac_weeks'] = hadlock.ga_for_ac(ac_mm)
    if fl_mm is not None:
        results['fl_weeks'] = hadlock.ga_for_fl(fl_mm)
    
    return results
