"""
SafeShift Index Service - Burnout risk calculation algorithm
Calculates SafeShift Index (0-100) based on shift parameters
"""


class SafeShiftService:
    """Calculate SafeShift Index and risk zone"""
    
    @staticmethod
    def calculate_index(hours_slept, shift_type, shift_length, patients_count, stress_level):
        """
        Calculate SafeShift Index (0-100)
        
        Args:
            hours_slept: Hours slept before shift (0-24)
            shift_type: 'day' or 'night'
            shift_length: Shift length in hours (1-24)
            patients_count: Number of patients
            stress_level: Subjective stress (1-10)
        
        Returns:
            tuple: (index, zone) where index is 0-100 and zone is 'green', 'yellow', or 'red'
        """
        
        index = 0
        
        # 1. Sleep Score (0-30 points)
        if hours_slept < 4:
            index += 30
        elif hours_slept < 5:
            index += 25
        elif hours_slept < 6:
            index += 20
        elif hours_slept < 7:
            index += 10
        
        # 2. Shift Type Score (0-25 points)
        if shift_type == 'night':
            index += 25
        else:
            index += 10
        
        # 3. Shift Length Score (0-20 points)
        if shift_length >= 24:
            index += 20
        elif shift_length >= 12:
            index += 15
        elif shift_length >= 8:
            index += 5
        
        # 4. Patients Score (0-15 points)
        if patients_count > 20:
            index += 15
        elif patients_count > 15:
            index += 10
        elif patients_count > 10:
            index += 5
        
        # 5. Stress Score (0-20 points)
        index += int((stress_level / 10) * 20)
        
        # Cap at 100
        index = min(index, 100)
        
        # Determine zone
        if index < 40:
            zone = 'green'
        elif index < 70:
            zone = 'yellow'
        else:
            zone = 'red'
        
        return index, zone
