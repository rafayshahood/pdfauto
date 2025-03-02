# --------------------------
# Helper functions for generating random values
import random

def get_random_bp(systolic_min=130, systolic_max=145, diastolic_min=65, diastolic_max=87):
    systolic = random.randint(systolic_min, systolic_max)
    diastolic = random.randint(diastolic_min, diastolic_max)
    return f"{systolic}/{diastolic}"

def get_random_value(min_value, max_value, roundTo=1, is_integer=False):
    value = random.uniform(min_value, max_value)
    if is_integer:
        return round(value)
    return round(value, roundTo)

def getRangeValues():
    tempVal = str(get_random_value(97.7, 99.5))
    hrVal = str(get_random_value(60, 100, is_integer=True))
    rrVal = str(get_random_value(16, 20, is_integer=True))
    oxygenVal = str(get_random_value(95, 99, is_integer=True))
    bsFastVal = str(get_random_value(140, 180, is_integer=True))
    bsRapidVal = str(get_random_value(190, 250, is_integer=True))
    random_bp = str(get_random_bp())
    return tempVal, hrVal, rrVal, oxygenVal, bsFastVal, bsRapidVal, random_bp

def getRangeValuesArray(noOfVal):
    # Generate arrays for n iterations.
    tempArray = []
    hrArray = []
    rrArray = []
    oxygenArray = []
    bsFastArray = []
    bsRapidArray = []
    random_bpArray = []

    for i in range(noOfVal):
        tempVal, hrVal, rrVal, oxygenVal, bsFastVal, bsRapidVal, random_bp = getRangeValues()
        tempArray.append(tempVal)
        hrArray.append(hrVal)
        rrArray.append(rrVal)
        oxygenArray.append(oxygenVal)
        bsFastArray.append(bsFastVal)
        bsRapidArray.append(bsRapidVal)
        random_bpArray.append(random_bp)
    return tempArray, hrArray, rrArray, oxygenArray, bsFastArray, bsRapidArray, random_bpArray 