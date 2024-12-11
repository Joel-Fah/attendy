import base64
import json
from collections import defaultdict
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


def group_model_items_by_week(queryset):
    """
    Group model items by week based on their creation date.

    This function takes a queryset of model items and groups them by the week in which they were created. The items are
    grouped based on the start of the week (Monday) for each item's creation date.

    Parameters:
    queryset (QuerySet): A queryset of model items to be grouped.

    Returns:
    dict: A dictionary where the keys are the week ranges (e.g., "Mon 19 Aug - Sun 25 Aug") and the values are lists
          of items created during that week.

    Example:
    {
        'Mon 19 Aug - Sun 25 Aug': [<Item1>, <Item2>, ...],
        'Mon 26 Aug - Sun 01 Sep': [<Item3>, <Item4>, ...],
        ...
    }
    """
    grouped_items = defaultdict(list)

    for item in queryset.order_by('created_at'):
        # Calculate the start of the week (Monday) for each item
        week_start = item.created_at - timedelta(days=item.created_at.weekday())
        week_end = week_start + timedelta(days=6)

        # Format the week range as "Mon 19 Aug - Sun 25 Aug"
        week_range = f"{week_start.strftime('%a %d %b')} - {week_end.strftime('%a %d %b %Y')}"

        # Group items by this week range
        grouped_items[week_range].append(item)

    return grouped_items


# Function that returns a list of FAQs (questions and answers) for display on the FAQ page.
def get_faqs():
    """
    Get a list of frequently asked questions (FAQs) for display on the FAQ page.

    Returns:
    list: A list of dictionaries, where each dictionary represents an FAQ item with 'question' and 'answer' keys.

    Example:
    [
        {'question': 'What is Lorem Ipsum?', 'answer': 'Lorem Ipsum is simply dummy text of the printing...'},
        {'question': 'Why do we use it?', 'answer': 'It is a long-established fact that a reader will be...'},
        ...
    ]
    """
    return [
        {
            'question': "Can I attend the same class twice in one day? Asking for a friend...",
            'answer': "Well, if you really love that class! As long as the start times are different, you're free to "
                      "double-dip on knowledge."
        },
        {
            'question': "What happens if I forget to take attendance? Does the world end?",
            'answer': "Good news—no apocalypse! But you might need to bribe your classmates for the notes. Don’t make "
                      "it a habit, though!"
        },
        {
            'question': "Why can’t I create two attendances for the same time and class? Magic?",
            'answer': "Almost! Time travel is tricky, and our system likes to keep things in order. One class, "
                      "one time. It’s the law of the universe… or at least, our app."
        }
    ]


def get_quotes():
    return [
        "Through the sleepless nights, the tears, the exhaustion, I nearly gave up so many times. But with every "
        "moment of doubt, I found strength by the grace of God. Now, as the project finally reaches its end, "
        "the relief and peace that fill my heart remind me—it was all worth it, every single struggle.",
        "I braced for it—the feedback, the judgment after all the sweat, tears, and sleepless nights. But hearing the "
        "voices of those who used it, who saw the work and felt its impact—it hit different. All the pain, doubt, "
        "and pushing through felt worth it in that moment. To know it mattered... that’s the reward no one tells you "
        "about.",
        "After countless sleepless nights, stress, and nearly giving up, seeing that long project finally come to an "
        "end brings a peace and joy like no other. Through pain and struggle, by God's grace, we kept pushing—and "
        "now, it’s all worth it.",
        "Don’t hold back—your feedback, even if tough to hear, is what drives real growth. It might sting, "
        "but it’s the key to making things better. Honest input, no matter how harsh, is a gift that leads to real "
        "progress.",
        "As the project nears its end, the finish line is in sight, but feedback reminds me there’s still work to be "
        "done. It’s not easy, but I know it’s the last push that makes the difference between good and great.",
        "I know the effort, the long hours, and the passion poured into this work. Giving feedback isn't about "
        "criticism; it’s about helping you reach the potential I see in what you’ve done. With empathy, "
        "we shape something stronger together.",
        "As the project was wrapping up, I figured I was done—ready to call it finished. But then came all the "
        "comments and suggestions. At first, I brushed them off, thinking it was good enough. But slowly, I realized "
        "that maybe those last changes were exactly what it needed to be something great.",
        "Giving feedback isn’t always easy—I know how much effort went into this. But offering honest critique, "
        "with empathy and understanding, is how we help each other grow and reach our best."
    ]


def encode_data(data):
    json_data = json.dumps(data)
    encoded_data = base64.urlsafe_b64encode(json_data.encode()).decode()
    return encoded_data


def decode_data(encoded_data):
    decoded_data = base64.urlsafe_b64decode(encoded_data.encode()).decode()
    return json.loads(decoded_data)

def date_formatter(date: datetime) -> str:
    """
    This function takes a date object and returns a string representation of the date in the format 'Monday 19 August 2021'.

    Args:
        date (datetime): The date to format.

    Returns:
        str: The formatted date string.
    """
    return date.strftime('%A %d %B %Y')

def short_date_formatter(date: datetime) -> str:
    """
        This function takes a date object and returns a string representation of the date in the format 'Mon. 19 Aug. 2021'.

        Args:
            date (datetime): The date to format.

        Returns:
            str: The formatted date string.
        """
    return date.strftime('%a. %d %b. %Y')

def time_formatter(time: datetime) -> str:
    """
    This function takes a time object and returns a string representation of the time in the format '12:00 PM'.

    Args:
        time (datetime): The time to format.

    Returns:
        str: The formatted time string.
    """
    return time.strftime('%I:%M %p')

def datetime_formatter(date_time: datetime) -> str:
    """
    This function takes a datetime object and returns a string representation of the datetime in the format 'Monday 19 August 2021, 12:00 PM'.

    Args:
        date_time (datetime): The datetime to format.

    Returns:
        str: The formatted datetime string.
    """
    return f"{date_formatter(date_time)} at {time_formatter(date_time)}"
