"""
Burnout Risk Prediction Service
Predict future burnout risk based on trends
"""

from datetime import timedelta, date
from sqlalchemy import and_
import statistics

class PredictionService:
    
    @staticmethod
    def predict_burnout_risk(db, Shift, user_id, days_ahead=14):
        """
        Predict burnout risk for next N days
        """
        
        # Get last 30 days of shifts
        start_date = date.today() - timedelta(days=30)
        
        shifts = Shift.query.filter(
            and_(
                Shift.UserId == user_id,
                Shift.ShiftDate >= start_date
            )
        ).order_by(Shift.ShiftDate.asc()).all()
        
        if len(shifts) < 3:
            return {
                'prediction': 'insufficient_data',
                'predicted_index': None,
                'confidence': 0,
                'days_until_critical': None,
                'reasoning': 'Not enough data to predict. Please log more shifts.'
            }
        
        # Calculate trend
        indices = [s.SafeShiftIndex for s in shifts]
        
        # Linear regression (simple)
        n = len(indices)
        x = list(range(n))
        y = indices
        
        # Calculate slope (trend)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Predict next value
        last_index = indices[-1]
        predicted_index = last_index + (slope * (days_ahead / len(shifts)))
        predicted_index = max(0, min(100, predicted_index))
        
        # ============================================
        # Determine Risk Level
        # ============================================
        
        if predicted_index >= 70:
            prediction = 'high_risk'
        elif predicted_index >= 50:
            prediction = 'medium_risk'
        else:
            prediction = 'low_risk'
        
        # ============================================
        # Calculate Days Until Critical (70+)
        # ============================================
        
        days_until_critical = None
        if slope > 0:
            if last_index < 70:
                days_needed = (70 - last_index) / (slope / len(shifts))
                days_until_critical = max(1, int(days_needed))
        
        # ============================================
        # Calculate Confidence
        # ============================================
        
        std_dev = statistics.stdev(indices) if len(indices) > 1 else 0
        confidence = 1.0 - (std_dev / 100)
        confidence = max(0.3, min(1.0, confidence))
        
        # ============================================
        # Generate Reasoning
        # ============================================
        
        if slope > 0.5:
            trend_desc = "rising (getting worse)"
        elif slope < -0.5:
            trend_desc = "falling (improving)"
        else:
            trend_desc = "stable"
        
        recent_avg = sum(indices[-7:]) / min(7, len(indices[-7:]))
        
        reasoning = f"Your SafeShift Index is {trend_desc}. Recent average: {recent_avg:.0f}. Predicted in {days_ahead} days: {predicted_index:.0f}."
        
        return {
            'prediction': prediction,
            'predicted_index': int(predicted_index),
            'confidence': round(confidence, 2),
            'days_until_critical': days_until_critical,
            'reasoning': reasoning,
            'slope': round(slope, 3),
            'current_index': last_index,
            'last_30_days_avg': round(sum(indices) / len(indices), 1)
        }
    
    @staticmethod
    def get_prediction_ai_message(llm_service, user_first_name, prediction_data):
        """
        Generate AI message about burnout prediction
        """
        
        if prediction_data['prediction'] == 'insufficient_data':
            return prediction_data['reasoning']
        
        pred_index = prediction_data['predicted_index']
        pred_level = prediction_data['prediction']
        days_until = prediction_data['days_until_critical']
        confidence = prediction_data['confidence']
        
        prompt = f"""Generate a SHORT prediction warning for {user_first_name} about their burnout risk in the next 14 days.

Prediction Data:
- Predicted SafeShift Index: {pred_index} (out of 100)
- Risk Level: {pred_level}
- Days until critical zone (70+): {days_until if days_until else 'N/A'}
- Confidence: {confidence * 100:.0f}%
- Reasoning: {prediction_data['reasoning']}

Task:
1. Be honest about the prediction
2. Suggest 2-3 PREVENTIVE actions they can take NOW
3. Keep it SHORT (2-3 sentences)
4. NOT scary, but realistic

Tone: Forward-looking and supportive.
"""
        
        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {"role": "system", "content": llm_service.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM Error in get_prediction_ai_message: {str(e)}")
            return f"Based on current trends, your burnout risk may increase in the next 2 weeks. Consider preventive measures now."
