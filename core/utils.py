from datetime import datetime, timedelta


def calculate_duration(start_time, end_time):
    """
    Calculate the duration between two time points.

    This function takes two time objects, `start_time` and `end_time`, and calculates the duration between them.
    If the duration is negative (i.e., `end_time` is before `start_time`), it assumes the end time is on the next day
    and adjusts the duration accordingly.

    Parameters:
    start_time (datetime.time): The start time.
    end_time (datetime.time): The end time.

    Returns:
    timedelta: The duration between the start and end times. If the end time is before the start time, the duration
               will be adjusted to account for the end time being on the next day.
    """
    today = datetime.today().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)
    duration = end_datetime - start_datetime
    if duration < timedelta(0):
        duration += timedelta(days=1)
    return duration


def is_valid_time(start_time, end_time):
    """
    Check if the end time comes after the start time.

    This function takes two time objects, `start_time` and `end_time`, and checks if the end time comes after the
    start time.

    Parameters:
    start_time (datetime.time): The start time.
    end_time (datetime.time): The end time.

    Returns:
    bool: True if the end time comes after the start time, False otherwise.
    """
    today = datetime.today().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)
    return end_datetime > start_datetime
