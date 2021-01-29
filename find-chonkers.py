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
    message = "%s: %s: %s\n %s" % (
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


def search_size(min_size=100000000):
    """Search the GitHub api based on finding repos greater than a minimum size."""
    url = "%s/search/repositories" % BASE
    headers = get_headers()

    # Create a query based on size
    query = "size:>%s" % min_size
    response = requests.get(url, params={"q": query}, headers=headers)
    if response.status_code != 200:
        abort_if_fail(response)

    results = response.json()
    print("Found %s results for size %s" % (results["total_count"], min_size))
    return {x["html_url"]: x for x in results["items"]}


def convert_size(size_bytes):
    # https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def main():

    # Get results and sort by size
    size = 100000000
    results = search_size(size)
    results = OrderedDict(sorted(results.items(), reverse=True, key = lambda x: getitem(x[1], 'size'))) 

    # Generate list of sizes (/assets/images/sizes/{1-6}.png
    sizes = [6, 5, 4, 4, 3, 3, 3, 2, 2]
    sizes = sizes + (len(results) - len(sizes)) * [1]

    # Write to output data file.
    output = os.path.join(here, "_data", "repos.yml")

    data = []
    for i, url in enumerate(results):
        result = results[url]
        entry = {
            "url": url,
            "owner": result["owner"]["login"],
            "avatar": result["owner"]["avatar_url"],
            "image": "/assets/images/sizes/%s.png" % sizes[i],
            "name": result["full_name"],
            "size": convert_size(result["size"]),
            "rawsize": result['size'],
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

    write_yaml({"chonkers": data}, output)
    # /assets/images/projects/redpineapple/desktop.jpg


if __name__ == "__main__":
    main()
