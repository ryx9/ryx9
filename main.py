import datetime
from dateutil import relativedelta
import time
from lxml import etree
import requests

# from dotenv import load_dotenv
import os


# load_dotenv()

# username = os.environ.get("USER_NAME")
# token = os.environ.get("ACCESS_TOKEN")
token = os.getenv("ACCESS_TOKEN")
username = os.getenv("USER_NAME")


def get_user_repos(username, token=None):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 100, "page": page, "sort": "updated"}
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()

        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1

    return repos


def get_follower_count(username, token=None):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/users/{username}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    return data["followers"], data["created_at"]  # this is your "196"


def get_commit_and_contrib_data(username, token, account_created_at):
    """
    Loops year by year since account creation (GraphQL's contributionsCollection
    caps at 1 year per query) and sums total commits + unique repos contributed to.
    """
    headers = {"Authorization": f"Bearer {token}"}
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalRepositoriesWithContributedCommits
        }
      }
    }
    """

    start = datetime.datetime.fromisoformat(account_created_at.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)

    total_commits = 0
    contributed_repos = (
        set()
    )  # can't dedupe repo names from this query alone; see note below

    current = start
    while current < now:
        year_end = min(current + relativedelta.relativedelta(years=1), now)
        variables = {
            "login": username,
            "from": current.isoformat(),
            "to": year_end.isoformat(),
        }
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()["data"]["user"]["contributionsCollection"]

        total_commits += data["totalCommitContributions"]
        contributed_repos_count = data["totalRepositoriesWithContributedCommits"]

        current = year_end

    return total_commits, contributed_repos_count


# def get_user_info(username, token=None):
#    headers = {"Accept": "application/vnd.github+json"}
#    if token:
#        headers["Authorization"] = f"Bearer {token}"
#    resp = requests.get(f"https://api.github.com/users/{username}", headers=headers)
#    resp.raise_for_status()
#    return resp.json()


def svg_overwrite(
    filename, age_data, repo_data, follower_data, star_data, commit_data, contrib_data
):
    # commit_data, star_data, repo_data, contrib_data, follower_data, loc_data):
    age_data_lenght = len(age_data)
    tree = etree.parse(filename)
    root = tree.getroot()
    justify_format(root, "age_data", age_data, (23 + age_data_lenght))
    justify_format(root, "commit_data", commit_data, 22)
    justify_format(root, "star_data", star_data, 14)
    justify_format(root, "repo_data", repo_data, 6)
    justify_format(root, "contrib_data", contrib_data)
    justify_format(root, "follower_data", follower_data, 10)
    # justify_format(root, 'loc_data', loc_data[2], 9)
    # justify_format(root, 'loc_add', loc_data[0])
    # justify_format(root, 'loc_del', loc_data[1], 7)
    tree.write(filename, encoding="utf-8", xml_declaration=True)


def justify_format(root, element_id, new_text, length=0):
    if isinstance(new_text, int):
        new_text = f"{'{:,}'.format(new_text)}"
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_map = {0: "", 1: " ", 2: ". "}
        dot_string = dot_map[just_len]
    else:
        dot_string = " " + ("." * just_len) + " "
    find_and_replace(root, f"{element_id}_dots", dot_string)


def find_and_replace(root, element_id, new_text):
    """
    Finds the element in the SVG file and replaces its text with a new value
    """
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


def daily_readme(birthday):
    """
    Returns the length of time since I was born
    e.g. 'XX years, XX months, XX days'
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return "{} {}, {} {}, {} {}{}".format(
        diff.years,
        "year" + format_plural(diff.years),
        diff.months,
        "month" + format_plural(diff.months),
        diff.days,
        "day" + format_plural(diff.days),
        " 🎂" if (diff.months == 0 and diff.days == 0) else "",
    )


def format_plural(unit):
    """
    Returns a properly formatted number
    e.g.
    'day' + format_plural(diff.days) == 5
    >>> '5 days'
    'day' + format_plural(diff.days) == 1
    >>> '1 day'
    """
    return "s" if unit != 1 else ""


def perf_counter(funct, *args):
    """
    Calculates the time it takes for a function to run
    Returns the function result and the time differential
    """
    start = time.perf_counter()
    funct_return = funct(*args)
    return funct_return, time.perf_counter() - start


if __name__ == "__main__":
    repos = get_user_repos(username, token)
    followers, created_at = get_follower_count(username, token)
    total_commits, contributed_repos_count = get_commit_and_contrib_data(
        username, token, created_at
    )
    print(total_commits, contributed_repos_count)
    repo_data = len(repos)
    star_count = sum(repo["stargazers_count"] for repo in repos)
    print(followers)
    age_data, age_time = perf_counter(daily_readme, datetime.datetime(2006, 1, 20))
    svg_overwrite(
        "darkmode.svg",
        age_data,
        repo_data,
        followers,
        star_count,
        total_commits,
        contributed_repos_count,
    )
    print(age_data, age_time)
