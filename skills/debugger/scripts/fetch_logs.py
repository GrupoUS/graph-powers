#!/usr/bin/env python3
"""fetch_logs.py - Debug Skill - Error Log Fetcher.
Aggregates logs from GitHub Actions, VPS containers, and the project's database
for error analysis.

Everything project-specific is read from environment variables:
  - GITHUB_REPO              owner/repo (defaults to git remote origin)
  - PROJECT_VPS_HOST         SSH host for container inspection (optional)
  - DB_STATUS_COMMAND        shell command printing database status (optional),
                             e.g. the hosting vendor's CLI status subcommand
  - DATABASE_URL             used only to print the slow-query hint (optional)
"""
import os
import shlex
import shutil
import subprocess


def detect_repo() -> str:
    """Resolve owner/repo: $GITHUB_REPO > git remote origin > config.json::project.name."""
    if os.environ.get("GITHUB_REPO"):
        return os.environ["GITHUB_REPO"]
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        url = r.stdout.strip()
        if url.startswith("git@github.com:"):
            return url.split(":", 1)[1].rstrip(".git")
        if url.startswith("https://github.com/"):
            return url.removeprefix("https://github.com/").rstrip(".git")
    except Exception:
        pass
    return ""


REPO = detect_repo()
VPS_HOST = os.environ.get("PROJECT_VPS_HOST", "")
DB_STATUS_COMMAND = os.environ.get("DB_STATUS_COMMAND", "")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                          timeout=30, check=False)


def has_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def fetch_gh_actions() -> None:
    print("🔄 GitHub Actions — Recent Runs:")
    print("─────────────────────────────────")
    if not has_command("gh"):
        print("⚠️  GitHub CLI not installed")
        print("   Install: brew install gh")
        print()
        return

    r = run([
        "gh", "run", "list", "--repo", REPO, "-L", "5",
        "--json", "status,conclusion,name,headBranch,createdAt",
        "--template",
        "{{range .}}{{.name}} | {{.headBranch}} | {{.conclusion}} | {{.createdAt}}\n{{end}}",
    ])
    print(r.stdout or "No runs available")
    print()

    # Last failed run
    r2 = run([
        "gh", "run", "list", "--repo", REPO, "-L", "1",
        "--status", "failure",
        "--json", "databaseId",
        "--template", "{{range .}}{{.databaseId}}{{end}}",
    ])
    failed_run = r2.stdout.strip()

    if failed_run:
        print(f"❌ Last Failed Run (ID: {failed_run}):")
        print("─────────────────────────────────")
        r3 = run(["gh", "run", "view", failed_run, "--repo", REPO, "--log-failed"])
        lines = r3.stdout.splitlines()
        print("\n".join(lines[-50:]))
        print()
    else:
        print("✅ No recent failed runs")
        print()


def fetch_vps_status() -> None:
    print("🖥️  VPS Container Status:")
    print("─────────────────────────")

    if not VPS_HOST:
        print("⚠️  VPS host not configured")
        print("   Set PROJECT_VPS_HOST to enable SSH log collection")
        print()
        return

    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
         f"root@{VPS_HOST}",
         "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"],
        capture_output=True, text=True, timeout=15, check=False,
    )
    if r.returncode == 0:
        print(r.stdout)
    else:
        print("⚠️  Cannot connect to VPS (SSH key, host, or network issue)")
        print(f"   Try: ssh root@{VPS_HOST}")
    print()


def fetch_db_status() -> None:
    print("🐘 Database Status:")
    print("──────────────────")
    if not DB_STATUS_COMMAND:
        print("⚠️  No database status command configured")
        print("   Set DB_STATUS_COMMAND to your provider's CLI status call")
        print("   (e.g. DB_STATUS_COMMAND='<vendor-cli> projects list')")
        print()
        return

    # POSIX mode eats backslashes, so a Windows path in the declared command is mangled.
    argv = shlex.split(DB_STATUS_COMMAND, posix=(os.name != "nt"))
    # shutil.which resolves PATHEXT on Windows (npm's .cmd shim); a subprocess "which" does not.
    binary = shutil.which(argv[0])
    if binary is None:
        print(f"⚠️  Command not found on PATH: {argv[0]}")
        print()
        return

    r = run([binary, *argv[1:]])
    print(r.stdout or "No database status output")
    print()
    print(
        "💡 For slow queries, run: psql \"$DATABASE_URL\" -c "
        + '"SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"'
    )


def main() -> None:
    print("📋 Fetching error logs...")
    print()
    fetch_gh_actions()
    fetch_vps_status()
    fetch_db_status()
    print("✅ Log fetch complete!")


if __name__ == "__main__":
    main()
