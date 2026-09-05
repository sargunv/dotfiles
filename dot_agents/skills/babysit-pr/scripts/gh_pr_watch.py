#!/usr/bin/env python3
"""Read-only PR watcher. Requires Python 3.10+ and authenticated GitHub CLI.

Copyright 2025 OpenAI. Licensed under Apache-2.0; see LICENSE.
Modified for these dotfiles: quiet polling, shared bot triage, explicit
acknowledgements, edited summaries, and conservative review freshness.
Source: https://github.com/openai/codex/blob/ddf04ad26789d040f9ef6a96736f76602e35a6cc/.codex/skills/babysit-pr/scripts/gh_pr_watch.py
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse


class GhCommandError(RuntimeError):
    pass


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


BOT_LOGINS = {
    "greptile-apps": "greptile",
    "greptile-apps-staging": "greptile",
    "chatgpt-codex-connector": "codex",
}


def bot_for(user):
    return BOT_LOGINS.get((user or {}).get("login", "").removesuffix("[bot]"))


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
            nodes { id isResolved isOutdated
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
    check_pages = gh_json(
        [
            "api",
            "--paginate",
            "--slurp",
            f"{base}/commits/{sha}/check-runs?per_page=100&filter=all",
        ]
    )
    checks = [c for p in check_pages for c in p["check_runs"]]
    statuses = api_list(f"{base}/commits/{sha}/statuses?per_page=100")
    # Keep the newest attempt within each suite, preserving distinct workflows.
    latest = {}
    for c in sorted(checks, key=lambda c: c["id"]):
        latest[(c["check_suite"]["id"], c["name"])] = {
            "name": c["name"],
            "url": c["html_url"],
            "state": c["conclusion"]
            if c["status"] == "completed"
            else "pending",
        }
    legacy = {}
    for s in sorted(statuses, key=lambda s: s["id"]):
        legacy[s["context"]] = {
            "name": s["context"],
            "url": s["target_url"],
            "state": s["state"],
        }
    # Read thread identities before their comments, so publishing a thread
    # between requests cannot make an already-observed finding disappear.
    threads = review_threads(repo, number)
    snapshot = {
        "pr": pr,
        "checks": list(latest.values()) + list(legacy.values()),
        "comments": api_list(f"{base}/issues/{number}/comments?per_page=100"),
        "reviews": api_list(f"{base}/pulls/{number}/reviews?per_page=100"),
        "inline": api_list(f"{base}/pulls/{number}/comments?per_page=100"),
        "threads": threads,
        "reactions": api_list(f"{base}/issues/{number}/reactions?per_page=100"),
    }
    roots = {c["id"] for c in snapshot["inline"] if not c.get("in_reply_to_id")}
    thread_roots = {
        thread["comments"]["nodes"][0]["databaseId"] for thread in threads
    }
    if roots != thread_roots:
        return None
    # Do not evaluate a mixture of two different heads collected during a push.
    after = gh_json(["api", f"{base}/pulls/{number}"])
    if after["head"]["sha"] != sha:
        return None
    snapshot["pr"] = after
    return snapshot


def fingerprint(kind, item):
    content = json.dumps(item, sort_keys=True).encode()
    return f"{kind}:{item['id']}:{hashlib.sha256(content).hexdigest()[:16]}"


def score(body):
    match = re.search(
        r"confidence(?:\s+score)?[^\d\n]{0,30}([0-5])\s*/\s*5", body, re.I
    )
    return int(match[1]) if match else None


def reviewed_head(body, sha):
    # Match an explicit review marker, not an incidental SHA in a finding.
    match = re.search(
        r"(?:last )?reviewed commit[^\n]{0,100}?\b([0-9a-f]{7,40})\b",
        body,
        re.I,
    )
    return bool(match and sha.startswith(match[1].lower()))


def evaluate(snapshot, state, expected=None):
    pr = snapshot["pr"]
    sha = pr["head"]["sha"]
    new_head = state.get("head") != sha or "baseline_reactions" not in state
    if expected is not None:
        state["required_bots"] = expected
    selected = state.get("required_bots")
    acknowledged = set(state.get("acknowledged", []))
    items, evidence = (
        [],
        {bot: [] for bot in set(selected or []) | set(state.get("bots", []))},
    )

    def add(kind, item, bot, **extra):
        token = fingerprint(kind, item)
        entry = dict(kind=kind, token=token, bot=bot, **item, **extra)
        # Threads must actually be resolved; seeing them does not acknowledge them.
        if kind == "thread" or token not in acknowledged:
            items.append(entry)

    for c in (
        snapshot["comments"]
        + snapshot["reviews"]
        + snapshot["inline"]
        + snapshot["reactions"]
    ):
        bot = bot_for(c.get("user"))
        if bot:
            evidence.setdefault(bot, [])
    for c in snapshot["comments"]:
        bot = bot_for(c.get("user"))
        if bot:
            # Codex maintains this activity table separately from its findings.
            # Its status edits neither require triage nor supersede a review.
            if bot == "codex" and c["body"].startswith(
                "<!-- codex-pull-request-review-summary -->"
            ):
                continue
            item = {k: c[k] for k in ("id", "body", "updated_at", "html_url")}
            if not (
                bot == "codex"
                and c["body"].partition("\n")[0]
                == "Codex Review: Didn't find any major issues. Hooray!"
            ):
                add("comment", item, bot)
            evidence[bot].append(
                (
                    c["updated_at"],
                    reviewed_head(c["body"], sha),
                    c["body"],
                    fingerprint("comment", item),
                )
            )
    for r in snapshot["reviews"]:
        bot = bot_for(r.get("user"))
        if bot and r["state"] not in {"PENDING", "DISMISSED"}:
            item = {
                k: r[k]
                for k in ("id", "body", "submitted_at", "html_url", "commit_id")
            }
            if r["body"].strip():
                add("review", item, bot)
            evidence[bot].append(
                (
                    r["submitted_at"],
                    r["commit_id"] == sha,
                    r["body"],
                    fingerprint("review", item),
                )
            )

    # Some Greptile installations put their summary in the PR description.
    body = pr.get("body") or ""
    if "greptile" in evidence and score(body) is not None:
        item = {"id": pr["number"], "body": body}
        add("description", item, "greptile")
        evidence["greptile"].append(
            (
                pr["updated_at"],
                reviewed_head(body, sha),
                body,
                fingerprint("description", item),
            )
        )

    inline = {c["id"]: c for c in snapshot["inline"]}
    for thread in snapshot["threads"]:
        if thread["isResolved"]:
            continue
        root = thread["comments"]["nodes"][0]["databaseId"]
        comments = [
            c
            for c in inline.values()
            if c["id"] == root or c.get("in_reply_to_id") == root
        ]
        bots = [
            bot_for(c.get("user")) for c in comments if bot_for(c.get("user"))
        ]
        if bots:
            add(
                "thread",
                {
                    "id": thread["id"],
                    "outdated": thread["isOutdated"],
                    "comments": [
                        {
                            k: c.get(k)
                            for k in (
                                "id",
                                "body",
                                "user",
                                "path",
                                "line",
                                "original_line",
                                "commit_id",
                                "updated_at",
                                "html_url",
                            )
                        }
                        for c in comments
                    ],
                },
                bots[0],
            )

    reactions = {}
    for r in snapshot["reactions"]:
        bot = bot_for(r.get("user"))
        if bot:
            reactions.setdefault(bot, []).append(r)
    if new_head:
        state.update(
            head=sha,
            baseline_reactions=[r["id"] for r in snapshot["reactions"]],
            baseline_reviews=[
                r[3] for reviews in evidence.values() for r in reviews
            ],
        )
    bots = {}
    for bot, reviews in evidence.items():
        signals = reactions.get(bot, [])
        latest = max(reviews, default=None, key=lambda r: r[0])
        current = latest if latest and latest[1] else None
        fresh = [
            r
            for r in signals
            if r["id"] not in state["baseline_reactions"]
            or (current and r["created_at"] >= current[0])
        ]
        running = any(r["content"] == "eyes" for r in signals)
        # PR reactions are not SHA-bound. Require observation during this head
        # or a corroborating current review; other thumbs stay unverified.
        stale_review_in_watch = bool(
            latest
            and not current
            and latest[3] not in state["baseline_reviews"]
        )
        thumbs = not stale_review_in_watch and any(
            r["content"] == "+1"
            and (latest is None or r["created_at"] >= latest[0])
            for r in fresh
        )
        scored = [r for r in reviews if r[1] and score(r[2]) is not None]
        latest_score = max(scored, default=None, key=lambda r: r[0])
        rating = (
            score(latest_score[2])
            if latest_score and bot == "greptile"
            else None
        )
        complete = bool(current or thumbs) and not running
        clean = complete and (rating == 5 if bot == "greptile" else thumbs)
        bots[bot] = {
            "required": selected is None or bot in selected,
            "complete": complete,
            "clean": clean,
            "score": rating,
            "running": running,
            "reactions": [r["content"] for r in signals],
        }
    state["bots"] = sorted(bots)

    checks = snapshot["checks"]
    failures = [
        c
        for c in checks
        if c["state"] not in {"success", "neutral", "skipped", "pending"}
    ]
    pending = [c for c in checks if c["state"] == "pending"]
    required = [b for b in bots.values() if b["required"]]
    complete = all(b["complete"] for b in required)
    if pr["state"] != "open":
        event = "closed"
    elif items or failures or pr["mergeable"] is False:
        event = "action_required"
    elif pending or pr["mergeable"] is None or not complete:
        event = "waiting"
    elif pr["draft"] or pr["mergeable_state"] not in {
        "clean",
        "unstable",
        "has_hooks",
    }:
        event = "blocked"
    else:
        event = "clean" if all(b["clean"] for b in required) else "handled"
    state["offered"] = [i["token"] for i in items if i["kind"] != "thread"]
    return {
        "event": event,
        "url": pr["html_url"],
        "head": sha,
        "bots": bots,
        "items": items,
        "failed_checks": failures,
        "pending_checks": pending,
        "mergeable": pr["mergeable"],
        "mergeable_state": pr["mergeable_state"],
        "draft": pr["draft"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr", default="auto", help="PR number, URL, or auto (current branch)"
    )
    parser.add_argument("--repo", help="OWNER/REPO")
    parser.add_argument("--state-file", required=True, type=Path)
    parser.add_argument(
        "--bots",
        nargs="*",
        choices=("greptile", "codex"),
        default=None,
        help="Require only these bots; default: auto-detect from PR activity",
    )
    parser.add_argument(
        "--ack",
        nargs="+",
        metavar="TOKEN",
        help="Acknowledge handled summary/review tokens from the last output",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Poll quietly until work or a terminal state",
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
    repo, number = resolve_pr(args.pr, args.repo)
    key = f"{repo}#{number}"
    if state.get("pr", key) != key:
        raise ValueError("Use a separate state file for each PR")
    state["pr"] = key
    if args.ack:
        if not set(args.ack) <= set(state.get("offered", [])):
            raise ValueError(
                "Only tokens from the last snapshot can be acknowledged"
            )
        state["acknowledged"] = sorted(
            set(state.get("acknowledged", [])) | set(args.ack)
        )
        save_state(args.state_file, state)
        print(json.dumps({"event": "acknowledged", "tokens": args.ack}))
        return
    deadline = time.monotonic() + args.timeout_seconds
    ready = None
    while True:
        snapshot = fetch(repo, number)
        if snapshot is None:
            result = {
                "event": "waiting",
                "reason": "snapshot_changed_during_fetch",
            }
        else:
            result = evaluate(snapshot, state, args.bots)
            save_state(args.state_file, state)
        # Give newly queued CI/bots a poll to appear before declaring readiness.
        candidate = (result.get("head"), result["event"])
        if (
            args.watch
            and result["event"] in {"clean", "handled"}
            and candidate != ready
        ):
            ready = candidate
            result = dict(
                result, event="waiting", reason="confirming_readiness"
            )
        elif result["event"] == "waiting":
            ready = None
        if result["event"] != "waiting" or not args.watch:
            print(json.dumps(result))
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            result["event"] = "timeout"
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
