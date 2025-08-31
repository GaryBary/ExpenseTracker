from datetime import date

def fy_range_for_date(d: date):
    y = d.year
    in_fy = y if d >= date(y, 7, 1) else y - 1
    start = date(in_fy, 7, 1)
    end = date(in_fy + 1, 6, 30)
    label = f"FY{str(in_fy)[2:]}/{str(in_fy+1)[2:]}"
    return start, end, label
