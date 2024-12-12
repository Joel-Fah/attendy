import base64
import json
from collections import defaultdict
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Paragraph, Table, TableStyle, HRFlowable, Spacer
)


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
        },
        # about generating PDFs
        {
            'question': "Can I download the PDF of any attendance record?",
            'answer': "Absolutely! Just head to the attendance page and click the print button. It’s like magic, "
                      "but with more paper."
        },
        {
            'question': "Can I export to PDF the teaching records for any attendance?",
            'answer': "You bet! Just go to the teaching record\'s details page and click the print record button. It’s like having "
                      "your own personal archive, but without the dust."
        },
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
    """
    Decode the encoded data and return the original data.

    Args:
        encoded_data (str): The encoded data to decode.

    Returns:
        dict: The original data.
    """
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


def handle_inline_tags(text):
    """
    Converts custom inline HTML tags into ReportLab's mini-HTML markup.

    Args:
        text (str): The HTML text to process.

    Returns:
        str: The processed text with custom inline tags converted to ReportLab's mini-HTML markup.
    """
    replacements = {
        '<b>': '<b>', '</b>': '</b>',
        '<strong>': '<b>', '</strong>': '</b>',
        '<i>': '<i>', '</i>': '</i>',
        '<em>': '<i>', '</em>': '</i>',
        '<u>': '<u>', '</u>': '</u>',
        '<s>': '<strike>', '</s>': '</strike>',
        '<sub>': '<sub rise="0" size="-4">', '</sub>': '</sub>',
        '<sup>': '<super rise="6" size="-4">', '</sup>': '</super>',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Handle <a> links to make them blue, underlined, and clickable
    soup = BeautifulSoup(text, 'html.parser')
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '#')
        link_text = a_tag.get_text()  # Extracts only the inner text of the <a> tag

        # Create a ReportLab-style link with proper formatting
        styled_link = f'<a href="{href}" color="blue" fontName="Helvetica" underline="true" underlineColor="blue">{link_text}</a>'
        a_tag.replace_with(BeautifulSoup(styled_link, 'html.parser').a)

    # Handle <blockquote> tags to add a left indent and italic style and remove the class attribute
    for blockquote in soup.find_all('blockquote'):
        blockquote['style'] = 'margin-left: 20px; font-style: italic;'
        blockquote.attrs.pop('class', None)

    return str(soup)


def parse_html_to_flowables(html, styles):
    """
    Parses the HTML and converts it to ReportLab flowables.

    Args:
        html (str): The HTML content to parse.
        styles (dict): The styles to apply to the flowables.

    Returns:
        list: The list of ReportLab flowables.
    """
    soup = BeautifulSoup(html, 'html.parser')
    flowables = []

    for element in soup.children:
        if element.name == 'p':
            text = handle_inline_tags(str(element))
            para = Paragraph(text, styles['Normal'])
            flowables.append(para)

        elif element.name in ['ul', 'ol']:
            for index, li in enumerate(element.find_all('li'), start=1):
                marker = '•' if element.name == 'ul' else f'{index}.'  # "•" for ul, 1., 2., 3. for ol
                li_text = handle_inline_tags(str(li))
                para = Paragraph(f'{marker} {li_text}',
                                 style=ParagraphStyle(name='ListStyle', parent=styles['Normal'], leftIndent=20))
                flowables.append(para)

        elif element.name == 'table':
            table_data = []
            for row in element.find_all('tr'):
                row_data = []
                for cell in row.find_all(['th', 'td']):
                    cell_text = handle_inline_tags(str(cell))
                    cell_para = Paragraph(cell_text, styles['Normal'])
                    row_data.append(cell_para)
                table_data.append(row_data)

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightslategrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            flowables.append(table)
            flowables.append(Spacer(1, 8))

        elif element.name == 'hr':
            flowables.append(Spacer(1, 8))
            flowables.append(HRFlowable(width="100%", thickness=0.75))  # Adds a line break to simulate <hr>
            flowables.append(Spacer(1, 8))

        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(element.name[1])
            style = styles[f'Heading{level}']
            text = handle_inline_tags(str(element))
            para = Paragraph(text, style)
            flowables.append(para)

        elif element.name == 'blockquote':
            text = handle_inline_tags(str(element))
            blockquote_style = ParagraphStyle(name='BlockQuote', parent=styles['Italic'], fontSize=12, leftIndent=20,
                                              rightIndent=20, backColor=colors.HexColor("#F5F5F5"), borderPadding=8)
            para = Paragraph(text, blockquote_style)
            flowables.append(Spacer(1, 10))
            flowables.append(para)
            flowables.append(Spacer(1, 10))

        elif element.name in ['code', 'pre']:
            text = handle_inline_tags(str(element))
            code_style = ParagraphStyle(name='Code', parent=styles['Code'], fontName='Courier', fontSize=12,
                                        textColor=colors.red, borderPadding=(0, 4, 0, 4))
            para = Paragraph(text, code_style)
            flowables.append(para)

        elif element.name is None and element.strip():
            text = handle_inline_tags(str(element))
            para = Paragraph(text, styles['Normal'])
            flowables.append(para)

    return flowables
