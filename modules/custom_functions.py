# Given pound value of either XX or XX.XX, calculate the pence equivalent
def calculate_pence(current_value):
    float_value = float(current_value)
    pence_value = float_value * 100
    int_value   = int(pence_value)

    return int_value

# Given pence value, format into pounds XX.XX
def format_pounds(pence_value):
    pound_value  = pence_value / 100
    pound_format = '{:20,.2f}'.format(pound_value).replace(' ', '')

    return pound_format

# Return month number and name
def get_months():
    import calendar
    all_months = []
    for i in range(1, 13):
        all_months.append((i, calendar.month_name[i]))

    return all_months

# Return years from current year to 20 years in future
def get_years():
    import time
    current_year = int(time.strftime('%y'))
    all_years    = []

    for i in range (0, 21):
        all_years.append(current_year+i)

    return all_years
