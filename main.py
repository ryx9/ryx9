import datetime
from dateutil import relativedelta
from lxml import etree


def daily_readme(birthday):
    """
    Returns the length of time since I was born
    e.g. 'XX years, XX months, XX days'
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')


def format_plural(unit):
    """
    Returns a properly formatted number
    e.g.
    'day' + format_plural(diff.days) == 5
    >>> '5 days'
    'day' + format_plural(diff.days) == 1
    >>> '1 day'
    """
    return 's' if unit != 1 else ''


def find_and_replace(root, element_id, new_text):
    """
    Finds the element in the SVG file and replaces its text with a new value
    """
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


def svg_overwrite(filename, age_data):
    """
    Parse the SVG file and update the uptime/age element
    """
    tree = etree.parse(filename)
    root = tree.getroot()
    find_and_replace(root, 'age_data', age_data)
    tree.write(filename, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    age_data = daily_readme(datetime.datetime(2005, 5, 9))
    svg_overwrite('darkmode.svg', age_data)
    print(age_data)
