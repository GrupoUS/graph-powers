#!/usr/bin/env python3
"""Fetch one canonical issue through gh with a finite request timeout."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import urlsplit

FETCH_TIMEOUT_SECONDS = 30
ISSUE_FIELDS = "number,title,body,state,labels,author,url,createdAt,closedAt,comments"


class Blocked(Exception):
    """The issue reference, CLI result, or response cannot be used safely."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Blocked("required arguments: --repo HOST/OWNER/REPO --issue NUMBER-OR-URL")


def resolve_reference(issue, repository):
    match = re.fullmatch(r"([^/]+)/([^/]+)/([^/]+)", repository)
    if not match:
        raise Blocked("--repo must be the resolved host/owner/repository")
    parts = match.groups()
    if (
        not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", parts[0])
        or ".." in parts[0]
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", parts[1])
        or not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[2])
        or parts[2] in (".", "..")
    ):
        raise Blocked("--repo must be the resolved host/owner/repository")

    issue = issue.removeprefix("#")
    if re.fullmatch(r"[1-9][0-9]*", issue):
        return issue, parts

    try:
        target = urlsplit(issue)
        path = re.fullmatch(
            r"/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)/issues/([1-9][0-9]*)",
            target.path,
        )
        valid_host = re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", target.netloc)
        if (
            target.geturl() != issue
            or target.scheme != "https"
            or not valid_host
            or ".." in target.netloc
            or target.query
            or target.fragment
            or not path
            or target.netloc.lower() != parts[0].lower()
            or path[1].lower() != parts[1].lower()
            or path[2].lower() != parts[2].lower()
        ):
            raise ValueError
    except ValueError as error:
        raise Blocked("--issue URL must be the canonical HTTPS issue from the resolved repository") from error
    return issue, parts


def validate_issue(payload, repository_parts, reference):
    if not isinstance(payload, dict):
        raise Blocked("gh issue view returned an invalid issue object")
    required = {
        "number",
        "title",
        "body",
        "state",
        "labels",
        "author",
        "url",
        "createdAt",
        "closedAt",
        "comments",
    }
    if not required.issubset(payload):
        raise Blocked("gh issue view returned incomplete issue fields")
    if (
        type(payload["number"]) is not int
        or payload["number"] <= 0
        or not isinstance(payload["title"], str)
        or not isinstance(payload["body"], (str, type(None)))
        or not isinstance(payload["state"], str)
        or not isinstance(payload["labels"], list)
        or not isinstance(payload["author"], dict)
        or not isinstance(payload["createdAt"], str)
        or not isinstance(payload["closedAt"], (str, type(None)))
        or not isinstance(payload["comments"], list)
    ):
        raise Blocked("gh issue view returned malformed issue fields")
    canonical, _ = resolve_reference(payload["url"], "/".join(repository_parts))
    if canonical != payload["url"]:
        raise Blocked("gh issue view returned a noncanonical issue URL")
    expected_number = reference if reference.isdigit() else urlsplit(reference).path.rsplit("/", 1)[1]
    if int(expected_number) != payload["number"]:
        raise Blocked("gh issue view returned an issue number that does not match the request")
    return payload


def fetch_issue(issue, repository):
    reference, repository_parts = resolve_reference(issue, repository)
    argv = ["gh", "issue", "view", reference, "--repo", repository, "--json", ISSUE_FIELDS]
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            encoding="utf-8",
            timeout=FETCH_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise Blocked("gh is unavailable; expose the existing CLI") from error
    except subprocess.TimeoutExpired as error:
        raise Blocked("issue retrieval exceeded the 30-second limit; no retry was attempted") from error
    except OSError as error:
        raise Blocked("gh could not start") from error
    if result.returncode:
        raise Blocked(f"gh issue view failed (exit {result.returncode})")
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError) as error:
        raise Blocked("gh issue view returned invalid JSON") from error
    return validate_issue(payload, repository_parts, reference)


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", required=True)
    try:
        args = parser.parse_args(argv)
        issue = fetch_issue(args.issue, args.repo)
    except Blocked as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(issue, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
