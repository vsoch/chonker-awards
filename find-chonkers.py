#!/usr/bin/env python3

from collections import OrderedDict
import math
from operator import getitem
import os
import json
import requests
import sys
import time
import yaml

BASE = "https://api.github.com"
here = os.path.dirname(os.path.abspath(__file__))


def write_yaml(yaml_dict, filename):
    """write a dictionary to yaml file

    Arguments:
     - yaml_dict (dict) : the dict to print to yaml
     - filename (str) : the output file to write to
     - pretty_print (bool): if True, will use nicer formatting
    """
    with open(filename, "w") as filey:
        filey.writelines(yaml.dump(yaml_dict))
    return filename


def abort_if_fail(response):
    """Exit with an error and print the reason.

    Parameters:
    response (requests.Response) : an unparsed response from requests
    reason                 (str) : a message to print to the user for fail.
    """
    message = "%s: %s\n %s" % (
        response.status_code,
        response.reason,
        response.json(),
    )
    sys.exit(message)


def get_headers():
    """Return headers, including a GitHub token if it's defined"""
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = "token %s" % token
    return headers


def search_repos(user):
    """Search the GitHub api based on finding repos greater than a minimum size."""
    url = "%s/users/%s/repos" % (BASE, user)
    headers = get_headers()
    page = 1

    data = {"per_page": 100, "page": page}
    response = requests.get(url, headers=headers, params=data)
    repos = []
    while response.json():

        # Ensure the response is still working
        if response.status_code != 200:
            abort_if_fail(response)

        data["page"] += 1
        repos += response.json()
        response = requests.get(url, headers=headers, params=data)

    print("Found %s results for user %s" % (len(repos), user))
    return repos


def search_files(user, min_size=100000000):
    """Search the GitHub api based on finding repos greater than a minimum size."""
    url = "%s/search/code" % BASE
    headers = get_headers()

    # Create a query based on size
    data = dict()

    # 10 for each of 6 categories
    while len(data) < 60:
        query = "user:%s size:>%s" % (user, min_size)
        params = {"per_page": 100, "page": 1, "q": query}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            abort_if_fail(response)

        print("Found %s results" % response.json()["total_count"])
        lookup = {x["url"]: x for x in response.json()["items"]}
        data.update(lookup)
        min_size = min_size - 10000000
        time.sleep(2)

    data = list(data.values())

    # The metadata does not include size, so we will calculate for each
    for item in data:
        download_url = (
            item["html_url"]
            .replace("https://github.com", "https://raw.githubusercontent.com")
            .replace("/blob/", "/")
        )
        response = requests.head(download_url)
        item["size"] = int(response.headers["Content-Length"])

    return data


def get_size_name(size):
    lookup = {
        1: "A Fine Boi",
        2: "He Chomnk",
        3: "A Heckin' Chonker",
        4: "HEFTYCHONK",
        5: "MEGA CHONKER",
        6: "OH LAWD HE COMIN",
    }
    return lookup.get(size) or "A Fine Boi"


def convert_size(size_bytes):
    # https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def chonker_repos(user):

    # Get results and sort by size
    repos = search_repos(user)
    repos = sorted(repos, key=lambda i: i["size"], reverse=True)

    # Take top 10 for each group
    sizes = []
    for size in [6, 5, 4, 3, 2, 1]:
        sizes = sizes + [size] * 10

    repos = repos[: len(sizes)]

    data = []
    for i, result in enumerate(repos):
        size_name = get_size_name(sizes[i])
        entry = {
            "url": result["html_url"],
            "owner": result["owner"]["login"],
            "avatar": result["owner"]["avatar_url"],
            "image": "/assets/images/sizes/%s.png" % sizes[i],
            "name": result["full_name"],
            "size_name": size_name,
            # the repos results are returned in kilobytes
            "size": "%s MB" % round(result["size"] / 1000, 2),
            "rawsize": result["size"],
        }
        for field in [
            "stargazer_count",
            "watchers_count",
            "html_url",
            "created_at",
            "updated_at",
            "homepage",
            "language",
            "open_issues_count",
            "forks",
            "default_branch",
        ]:
            entry.update({field: result.get(field)})
        data.append(entry)

    # Write to output data file.
    output = os.path.join(here, "_data", "repos.yml")
    write_yaml({"chonkers": data}, output)


def chonker_files(user):

    # Get results and sort by size
    results = search_files(user)
    results = sorted(results, key=lambda i: i["size"], reverse=True)

    # Generate list of sizes (/assets/images/sizes/{1-6}.png
    sizes = []
    for size in [6, 5, 4, 3, 2, 1]:
        sizes = sizes + [size] * 10

    data = []
    for i, result in enumerate(results):

        # Get the size, or default to smallest
        try:
            size = sizes[i]
        except:
            size = 1

        entry = {
            "url": result["html_url"],
            "image": "/assets/images/sizes/%s.png" % size,
            "name": result["repository"]["full_name"] + ": " + result["path"],
            "size": convert_size(result["size"]),
            "size_name": get_size_name(size),
            "rawsize": result["size"],
        }
        data.append(entry)

    # Only keep top 60, 6 for each category
    data = data[:60]

    # Write to output data file.
    output = os.path.join(here, "_data", "files.yml")
    write_yaml({"chonkers": data}, output)


def main():

    # A username is required
    if len(sys.argv) == 1:
        sys.exit("A username is required.")
    user = sys.argv[1]

    chonker_repos(user)
    chonker_files(user)


if __name__ == "__main__":
    main()
