# get values within range
import random

def get_random_bp(systolic_min=130, systolic_max=145, diastolic_min=65, diastolic_max=87):
    systolic = random.randint(systolic_min, systolic_max)
    diastolic = random.randint(diastolic_min, diastolic_max)
    return f"{systolic}/{diastolic}"

def get_random_value(min_value, max_value, roundTo=1, is_integer=False):
    value = random.uniform(min_value, max_value)
    if is_integer:
        return round(value)  # Round to the nearest integer
    return round(value, roundTo)  # Otherwise, round to the specified decimal places

def getRangeValues():
    # Temp Range
    tempVal = str(get_random_value(97.7, 99.5))
    
    # Heart Rate (rounded to nearest integer)
    hrVal = str(get_random_value(60, 100, is_integer=True))
    
    # RR Range
    rrVal = str(get_random_value(16, 20, is_integer=True))
    
    # Oxygen Range
    oxygenVal = str(get_random_value(95, 99, is_integer=True))
    
    # BS if Fasting (rounded to nearest integer)
    bsFastVal = str(get_random_value(140, 180, is_integer=True))
    
    # BS if Rapid (rounded to nearest integer)
    bsRapidVal = str(get_random_value(190, 250, is_integer=True))
    
    # Blood Pressure
    random_bp = str(get_random_bp())

    return tempVal, hrVal, rrVal, oxygenVal, bsFastVal, bsRapidVal, random_bp


