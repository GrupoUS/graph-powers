#!/usr/bin/env python3
"""Preview, then explicitly publish one author-owned, marked issue-plan comment."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

MARKER = "<!-- graph-powers:issue-improve -->"


class Blocked(Exception):
    """An input or API result cannot safely select the intended comment."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Blocked("required arguments: --issue-url URL --body-file FILE [--publish]")


def api(host, endpoint, method="GET", body=None):
    argv = ["gh", "api", endpoint, "--hostname", host, "--method", method]
    payload = None
    if body is not None:
        argv.extend(["--input", "-"])
        payload = json.dumps({"body": body}, ensure_ascii=False)
    try:
        result = subprocess.run(
            argv,
            input=payload,
            capture_output=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
    except FileNotFoundError as error:
        raise Blocked("gh is unavailable; install or expose the existing CLI") from error
    except subprocess.TimeoutExpired as error:
        raise Blocked(f"gh {method} timed out; rerun to read comments before any write") from error
    except OSError as error:
        raise Blocked("gh could not start") from error
    if result.returncode:
        # Keep the deciding HTTP status, never arbitrary stderr (tokens, bodies or personal data).
        status = re.search(r"\bHTTP[ /]+([1-5][0-9]{2})\b", result.stderr)
        detail = f"; HTTP {status[1]}" if status else ""
        raise Blocked(
            f"gh {method} {endpoint.split('?')[0]} failed (exit {result.returncode}{detail})"
        )
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise Blocked(f"gh {method} returned invalid JSON; rerun with a fresh read") from error


def positive_id(value):
    return type(value) is int and value > 0


def comment_url(comment, issue_url):
    value = comment.get("html_url")
    if not isinstance(value, str) or not re.fullmatch(
        re.escape(issue_url) + r"#issuecomment-[1-9][0-9]*", value
    ):
        raise Blocked("API returned an invalid comment URL; rerun with a fresh read")
    return value


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--issue-url", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument(
        "--publish", action="store_true", help="caller has approved this exact target and payload"
    )
    args = parser.parse_args()
    try:
        target = urlsplit(args.issue_url)
        path = re.fullmatch(
            r"/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)/issues/([1-9][0-9]*)", target.path
        )
        valid_host = re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", target.netloc)
        if (
            target.geturl() != args.issue_url
            or target.scheme != "https"
            or not valid_host
            or ".." in target.netloc
            or target.query
            or target.fragment
            or not path
            or path[2] in (".", "..")
        ):
            raise ValueError
    except ValueError as error:
        raise Blocked("--issue-url must be the fetched canonical HTTPS issue URL") from error
    try:
        body = Path(args.body_file).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise Blocked("--body-file must be a readable UTF-8 draft") from error
    lines = body.splitlines()
    if not lines or lines[0] != MARKER or not "\n".join(lines[1:]).strip():
        raise Blocked(
            "draft must start with the standalone issue-improve marker and contain a plan"
        )
    if len(body) > 65536:
        raise Blocked("draft exceeds GitHub's 65,536-character comment limit; shorten the plan")
    if not args.publish:
        print(f"preview {args.issue_url}\n\n{body}", end="" if body.endswith("\n") else "\n")
        return 0

    host = target.netloc
    repo = f"repos/{path[1]}/{path[2]}"
    comments_endpoint = f"{repo}/issues/{path[3]}/comments"
    author = api(host, "user")
    if not isinstance(author, dict) or not positive_id(author.get("id")):
        raise Blocked("authenticated author is missing from gh api user")
    candidates = []
    page = 1
    while True:
        comments = api(host, f"{comments_endpoint}?per_page=100&page={page}")
        if not isinstance(comments, list):
            raise Blocked("API returned an invalid comment page")
        for comment in comments:
            if (
                not isinstance(comment, dict)
                or not positive_id(comment.get("id"))
                or not isinstance(comment.get("user"), dict)
                or not positive_id(comment["user"].get("id"))
                or not isinstance(comment.get("body"), str)
            ):
                raise Blocked("API returned an invalid comment")
            if comment["user"]["id"] == author["id"] and comment["body"].splitlines()[:1] == [
                MARKER
            ]:
                candidates.append(comment)
        if len(comments) < 100:
            break
        page += 1
    if len(candidates) > 1:
        raise Blocked("multiple own marked comments; resolve the duplicate targets before retrying")
    if candidates:
        selected = candidates[0]
        url = comment_url(selected, args.issue_url)
        if selected["body"] == body:
            print(f"unchanged {url}")
            return 0
        endpoint, method, outcome = f"{repo}/issues/comments/{selected['id']}", "PATCH", "updated"
    else:
        endpoint, method, outcome = comments_endpoint, "POST", "created"
    # Single-writer ceiling: GitHub offers no transactional marker upsert across publishers.
    # If concurrent publishing becomes necessary, coordinate externally before invoking this CLI.
    published = api(host, endpoint, method, body)
    if not isinstance(published, dict):
        raise Blocked("API returned an invalid write result; rerun with a fresh read")
    print(f"{outcome} {comment_url(published, args.issue_url)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Blocked as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(1) from None
