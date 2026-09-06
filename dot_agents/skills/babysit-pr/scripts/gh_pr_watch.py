#!/usr/bin/env python3
"""Read-only PR watcher. Requires Python 3.10+ and authenticated GitHub CLI.

Copyright 2025 OpenAI. Licensed under Apache-2.0; see LICENSE.
Modified for these dotfiles: complete activity collection and quiet change
detection. Review interpretation and readiness belong to the consuming agent.
Source: https://github.com/openai/codex/blob/ddf04ad26789d040f9ef6a96736f76602e35a6cc/.codex/skills/babysit-pr/scripts/gh_pr_watch.py
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse


class GhCommandError(RuntimeError):
    pass


class SnapshotChanged(RuntimeError):
    """Cross-request inconsistency; retry without replacing the baseline."""


def _format_gh_error(cmd, err):
    stdout = (err.stdout or "").strip()
    stderr = (err.stderr or "").strip()
    parts = [f"GitHub CLI command failed: {' '.join(cmd)}"]
    if stdout:
        parts.append(f"stdout: {stdout}")
    if stderr:
        parts.append(f"stderr: {stderr}")
    return "\n".join(parts)


def gh_text(args, repo=None):
    cmd = ["gh"]
    # `gh api` does not accept `-R/--repo` on all gh versions. The watcher's
    # API calls use explicit endpoints (e.g. repos/{owner}/{repo}/...), so the
    # repo flag is unnecessary there.
    if repo and (not args or args[0] != "api"):
        cmd.extend(["-R", repo])
    cmd.extend(args)
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as err:
        raise GhCommandError("`gh` command not found") from err
    except subprocess.CalledProcessError as err:
        raise GhCommandError(_format_gh_error(cmd, err)) from err
    return proc.stdout


def gh_json(args, repo=None):
    raw = gh_text(args, repo=repo).strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as err:
        raise GhCommandError(
            f"Failed to parse JSON from gh output for {' '.join(args)}"
        ) from err


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{path.name}.", suffix=".tmp", dir=path.parent
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(payload)
        os.replace(tmp_path, path)
    except Exception:
        with suppress(OSError):
            tmp_path.unlink(missing_ok=True)
        raise


def api_list(endpoint):
    pages = gh_json(["api", "--paginate", "--slurp", endpoint])
    return [item for page in pages for item in page]


def graphql(query, **variables):
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is not None:
            args.extend(["-F", f"{key}={value}"])
    result = gh_json(args)
    if result.get("errors"):
        raise GhCommandError(json.dumps(result["errors"]))
    return result["data"]


def review_threads(repo, number):
    owner, name = repo.split("/")
    query = """
    query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          reviewThreads(first: 100, after: $cursor) {
            nodes { id isResolved isOutdated path line startLine diffSide
              resolvedBy { login __typename }
              comments(first: 1) { nodes { databaseId } }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """
    result, cursor = [], None
    while True:
        data = graphql(
            query, owner=owner, name=name, number=number, cursor=cursor
        )
        page = data["repository"]["pullRequest"]["reviewThreads"]
        result.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return result
        cursor = page["pageInfo"]["endCursor"]


def ci_status(repo, sha):
    # GitHub owns job identity and rerun selection. Do not deduplicate names or
    # reconstruct readiness from individual historical check attempts.
    owner, name = repo.split("/")
    query = """
    query($owner: String!, $name: String!, $sha: GitObjectID!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        object(oid: $sha) { ... on Commit {
          statusCheckRollup {
            state
            contexts(first: 100, after: $cursor) {
              nodes {
                __typename
                ... on CheckRun {
                  id name detailsUrl status conclusion startedAt completedAt
                  checkSuite {
                    id app { slug name }
                    workflowRun { databaseId url }
                  }
                }
                ... on StatusContext {
                  id context targetUrl state description createdAt
                }
              }
              pageInfo { hasNextPage endCursor }
            }
          }
        } }
      }
    }
    """
    checks, cursor, initial_state = [], None, None
    while True:
        data = graphql(query, owner=owner, name=name, sha=sha, cursor=cursor)
        rollup = data["repository"]["object"]["statusCheckRollup"]
        state = rollup["state"] if rollup else None
        if cursor is None:
            initial_state = state
        elif state != initial_state:
            raise SnapshotChanged("CI rollup changed during pagination")
        if rollup is None:
            return {"state": None, "contexts": []}
        page = rollup["contexts"]
        checks.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return {"state": state, "contexts": checks}
        cursor = page["pageInfo"]["endCursor"]


def resolve_pr(pr_spec, repo):
    # Like upstream, resolve the base repository from the PR URL (fork-safe).
    args = ["pr", "view"] + ([] if pr_spec == "auto" else [pr_spec])
    data = gh_json(args + ["--json", "number,url"], repo=repo)
    url = urlparse(data["url"])
    if url.hostname != "github.com":
        raise ValueError("This watcher currently supports github.com only")
    return "/".join(url.path.strip("/").split("/")[:2]), data["number"]


def fetch(repo, number):
    base = f"repos/{repo}"
    pr = gh_json(["api", f"{base}/pulls/{number}"])
    sha = pr["head"]["sha"]
    ci = ci_status(repo, sha)
    # REST supplies full comment bodies and location metadata without the
    # nested GraphQL connection's per-thread pagination limit.
    threads = review_threads(repo, number)
    comments = api_list(f"{base}/issues/{number}/comments?per_page=100")
    reviews = api_list(f"{base}/pulls/{number}/reviews?per_page=100")
    inline = api_list(f"{base}/pulls/{number}/comments?per_page=100")
    reactions = api_list(f"{base}/issues/{number}/reactions?per_page=100")
    groups = {}
    for comment in inline:
        root = comment.get("in_reply_to_id") or comment["id"]
        groups.setdefault(root, []).append(comment)
    roots = {c["id"] for c in inline if not c.get("in_reply_to_id")}
    thread_roots = set()
    for thread in threads:
        nodes = thread["comments"]["nodes"]
        if not nodes:
            raise SnapshotChanged("Thread root missing during collection")
        root = nodes[0]["databaseId"]
        thread_roots.add(root)
        thread["comments"] = groups.get(root, [])
    if roots != thread_roots or set(groups) != roots:
        raise SnapshotChanged("Inline comments and thread roots disagree")
    after = gh_json(["api", f"{base}/pulls/{number}"])
    if after["head"]["sha"] != sha:
        raise SnapshotChanged("PR head changed during collection")
    return {
        "pr": after,
        "ci": ci,
        "comments": comments,
        "reviews": reviews,
        "threads": threads,
        "reactions": reactions,
    }


def fingerprints(snapshot):
    return {
        key: hashlib.sha256(
            json.dumps(value, sort_keys=True).encode()
        ).hexdigest()
        for key, value in snapshot.items()
    }


def observe(snapshot, state):
    hashes = fingerprints(snapshot)
    previous = state.get("hashes", {})
    changed = [key for key in hashes if hashes[key] != previous.get(key)]
    return {
        "event": "snapshot"
        if not previous
        else "changed"
        if changed
        else "unchanged",
        "changed": changed,
        "head_changed": bool(previous)
        and state["head"] != snapshot["pr"]["head"]["sha"],
        "snapshot": snapshot,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr", default="auto", help="PR number, URL, or auto (current branch)"
    )
    parser.add_argument("--repo", help="OWNER/REPO")
    parser.add_argument("--state-file", required=True, type=Path)
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Poll quietly until the snapshot changes; first run returns immediately",
    )
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    if args.poll_seconds < 1 or args.timeout_seconds < 1:
        parser.error("Polling interval and timeout must be positive")
    state = (
        json.loads(args.state_file.read_text())
        if args.state_file.exists()
        else {}
    )
    if state and state.get("version") != 2:
        raise ValueError("Incompatible watcher state; use a new state file")
    repo, number = resolve_pr(args.pr, args.repo)
    key = f"{repo}#{number}"
    if state.get("pr", key) != key:
        raise ValueError("Use a separate state file for each PR")
    deadline = time.monotonic() + args.timeout_seconds
    while True:
        snapshot = None
        try:
            snapshot = fetch(repo, number)
        except SnapshotChanged as error:
            result = {"event": "inconsistent", "reason": str(error)}
        else:
            result = observe(snapshot, state)
        remaining = deadline - time.monotonic()
        if (
            not args.watch
            or result["event"] in {"snapshot", "changed"}
            or remaining <= 0
        ):
            if args.watch and result["event"] in {"unchanged", "inconsistent"}:
                result["event"] = "timeout"
            # Only complete snapshots become a baseline. State records delivery,
            # never triage, approval, or readiness.
            if snapshot is not None:
                save_state(
                    args.state_file,
                    {
                        "version": 2,
                        "pr": key,
                        "head": snapshot["pr"]["head"]["sha"],
                        "hashes": fingerprints(snapshot),
                    },
                )
            print(json.dumps(result))
            return
        time.sleep(min(args.poll_seconds, remaining))


if __name__ == "__main__":
    try:
        main()
    except (GhCommandError, ValueError, OSError) as error:
        print(
            json.dumps({"event": "error", "message": str(error)}),
            file=sys.stderr,
        )
        sys.exit(1)
