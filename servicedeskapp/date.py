import datetime

current_datetime = datetime.datetime.now()

minute=current_datetime.minute
hour = current_datetime.hour
hour_to_minute = hour * 60
total_minutes = hour_to_minute + minute
if total_minutes >= 60:
    hour_convert = total_minutes // 60
    hour_12=hour_convert % 12
    if hour_12 ==0:
        hour_12=12  
    minute_convert = total_minutes % 60
    total=f"{hour_12} hr {minute_convert} min"
else:
    total=f"{total_minutes} min"


print(f"Current Datetime: {current_datetime}")
print(f"Extracted Hour: {hour}")
print(f"Extracted Minute: {minute}")
print(f"Time in Hours and Minutes: {total}")
print(f"Total Minutes since Midnight: {total_minutes}")
print(f"hour_convert: {hour_convert}")
