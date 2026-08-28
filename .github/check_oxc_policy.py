"""Check the committed TypeScript 7, Oxc and editor contract without node_modules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ZED_LANGUAGES = ("JavaScript", "TypeScript", "TSX", "JSON", "JSONC", "CSS")
ZED_CODE_LANGUAGES = ("JavaScript", "TypeScript", "TSX")
VSCODE_LANGUAGES = (
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact",
    "json",
    "jsonc",
    "css",
)
EXPECTED_OXFMT_FORMATTER = {"language_server": {"name": "oxfmt"}}
EXPECTED_OXFMT_FORMATTER_CHAIN = [EXPECTED_OXFMT_FORMATTER]
EXPECTED_INLAY_HINTS = {
    "enabled": True,
    "show_type_hints": True,
    "show_parameter_hints": True,
    "show_other_hints": True,
}
RETIRED_REFERENCE_EXCLUSIONS = {
    "CHANGELOG.md",
    "bun.lock",
    "docs/plans/2026-08-24-verify-runtime-performance.md",
}


def check_active_retired_references(problems: list[str]) -> None:
    """Reject retired JS/TS tooling in live artefacts while preserving historical records."""
    # Split the tokens so this checker does not report its own policy vocabulary.
    retired = (
        re.compile(r"\b" + "bi" + "ome" + r"\b"),
        re.compile(r"\b" + "ts" + "go" + r"\b"),
        re.compile("@" + "typescript/native-preview"),
        re.compile(r"(?<![A-Za-z0-9_-])" + "ts" + "c" + r"(?:\.(?:exe|cmd|js|cjs|mjs))?\b"),
        re.compile("130-bun-" + "ts" + "go" + "-gates\\.md"),
        re.compile("resource" + "Policy"),
    )
    text_suffixes = {
        ".json",
        ".js",
        ".mjs",
        ".md",
        ".py",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in RETIRED_REFERENCE_EXCLUSIONS or any(
            part in {".git", "node_modules", ".graph-powers"}
            for part in path.relative_to(ROOT).parts
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in retired:
            if pattern.search(text):
                problems.append(f"{relative} contains an active retired-tool reference")
                break


def load_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain an object")
    return value


def stable_typescript_declared(deps: dict[str, Any]) -> bool:
    value = deps.get("typescript")
    if not isinstance(value, str):
        return False
    return bool(re.search(r"(?:^|\D)7(?:\.\d+)?(?:\D|$)", value))


def check_zed(relative: str, problems: list[str]) -> None:
    zed = load_json(relative)
    if zed.get("line_ending") != "enforce_lf":
        problems.append(f"{relative} must enforce LF line endings")
    if zed.get("load_direnv") != "shell_hook":
        problems.append(f"{relative} must load direnv through the shell hook")
    if zed.get("format_on_save") != "on":
        problems.append(f"{relative} must enable global format_on_save")
    if zed.get("inlay_hints") != EXPECTED_INLAY_HINTS:
        problems.append(f"{relative} must enable the standard inlay hints")

    languages = zed.get("languages") or {}
    for language in ZED_LANGUAGES:
        settings = languages.get(language) or {}
        expected_formatter = (
            EXPECTED_OXFMT_FORMATTER
            if language in ZED_CODE_LANGUAGES
            else EXPECTED_OXFMT_FORMATTER_CHAIN
        )
        if settings.get("formatter") != expected_formatter:
            problems.append(f"{relative} {language} must use the Oxfmt language-server formatter")
        if settings.get("format_on_save") != "on":
            problems.append(f"{relative} {language} must enable format_on_save")
        if settings.get("prettier") != {"allowed": False}:
            problems.append(f"{relative} {language} must disable competing formatters")

    for language in ZED_CODE_LANGUAGES:
        settings = languages.get(language) or {}
        if settings.get("language_servers") != ["oxlint", "vtsls"]:
            problems.append(f"{relative} {language} must use exactly oxlint and vtsls")
    for language in ("JSON", "JSONC"):
        settings = languages.get(language) or {}
        if settings.get("language_servers") != ["..."]:
            problems.append(f"{relative} {language} must preserve the remaining language servers")
    css = languages.get("CSS") or {}
    if css.get("language_servers") != [
        "tailwindcss-intellisense-css",
        "!vscode-css-language-server",
        "...",
    ]:
        problems.append(f"{relative} CSS must keep Tailwind and disable the VS Code CSS server")

    lsp = zed.get("lsp") or {}
    oxlint = lsp.get("oxlint") or {}
    oxlint_init = oxlint.get("initialization_options") if isinstance(oxlint, dict) else None
    oxlint_options = oxlint_init.get("settings") if isinstance(oxlint_init, dict) else None
    if not isinstance(oxlint_options, dict) or oxlint_options.get("configPath") != ".oxlintrc.json":
        problems.append(f"{relative} Oxlint must use the root .oxlintrc.json")
    if (
        not isinstance(oxlint_options, dict)
        or oxlint_options.get("disableNestedConfig") is not True
    ):
        problems.append(f"{relative} Oxlint must disable nested configs")
    if (
        not isinstance(oxlint_options, dict)
        or oxlint_options.get("fixKind") != "safe_fix_or_suggestion"
    ):
        problems.append(f"{relative} Oxlint must allow safe fixes or suggestions")
    if not isinstance(oxlint_options, dict) or oxlint_options.get("typeAware") is not False:
        problems.append(f"{relative} Oxlint typeAware must be false")
    if not isinstance(oxlint_options, dict) or oxlint_options.get("run") != "onSave":
        problems.append(f"{relative} Oxlint must run onSave")
    if (
        not isinstance(oxlint_options, dict)
        or oxlint_options.get("unusedDisableDirectives") != "deny"
    ):
        problems.append(f"{relative} Oxlint must deny unused disable directives")

    oxfmt = lsp.get("oxfmt") or {}
    oxfmt_init = oxfmt.get("initialization_options") if isinstance(oxfmt, dict) else None
    oxfmt_options = oxfmt_init.get("settings") if isinstance(oxfmt_init, dict) else None
    if (
        not isinstance(oxfmt_options, dict)
        or oxfmt_options.get("fmt.configPath") != ".oxfmtrc.json"
    ):
        problems.append(f"{relative} Oxfmt must use the root .oxfmtrc.json")
    if (
        not isinstance(oxfmt_options, dict)
        or oxfmt_options.get("fmt.disableNestedConfig") is not True
    ):
        problems.append(f"{relative} Oxfmt must disable nested configs")
    if not isinstance(oxfmt_options, dict) or oxfmt_options.get("run") != "onSave":
        problems.append(f"{relative} Oxfmt must run onSave")

    vtsls = lsp.get("vtsls") or {}
    vtsls_settings = vtsls.get("settings") if isinstance(vtsls, dict) else None
    for language in ("TypeScript", "JavaScript"):
        settings = (
            (vtsls_settings or {}).get(language.lower())
            if isinstance(vtsls_settings, dict)
            else None
        )
        if (
            not isinstance(settings, dict)
            or settings.get("disableAutomaticTypeAcquisition") is not True
        ):
            problems.append(
                f"{relative} vtsls {language} must disable automatic TypeScript acquisition"
            )
        if isinstance(settings, dict) and "tsdk" in settings:
            problems.append(
                f"{relative} vtsls {language} must not define a workspace TypeScript SDK"
            )
        if (
            not isinstance(settings, dict)
            or (settings.get("preferences") or {}).get("importModuleSpecifier") != "non-relative"
        ):
            problems.append(f"{relative} vtsls {language} must prefer non-relative imports")
    typescript = (
        (vtsls_settings or {}).get("typescript") if isinstance(vtsls_settings, dict) else None
    )
    tsserver = typescript.get("tsserver") if isinstance(typescript, dict) else None
    if not isinstance(tsserver, dict) or tsserver.get("useSyntaxServer") != "never":
        problems.append(f"{relative} vtsls TypeScript must disable the syntax server")
    vtsls_options = (
        (vtsls_settings or {}).get("vtsls") if isinstance(vtsls_settings, dict) else None
    )
    if (
        not isinstance(vtsls_options, dict)
        or vtsls_options.get("autoUseWorkspaceTsdk") is not False
    ):
        problems.append(f"{relative} vtsls must use its bundled compatible TypeScript SDK")
    if (
        not isinstance(vtsls_options, dict)
        or vtsls_options.get("disableAutomaticTypeAcquisition") is not True
    ):
        problems.append(f"{relative} vtsls must disable automatic TypeScript acquisition globally")


def check_vscode(relative: str, problems: list[str]) -> None:
    vscode = load_json(relative)
    for language in VSCODE_LANGUAGES:
        settings = vscode.get(f"[{language}]") or {}
        if settings.get("editor.defaultFormatter") != "oxc.oxc-vscode":
            problems.append(f"{relative} {language} must use the Oxc formatter")
        if settings.get("editor.formatOnSave") is not True:
            problems.append(f"{relative} {language} must enable formatOnSave")


def check_extensions(relative: str, problems: list[str]) -> None:
    extensions = load_json(relative)
    if extensions.get("recommendations") != ["oxc.oxc-vscode"]:
        problems.append(f"{relative} must recommend only oxc.oxc-vscode")


def main() -> int:
    problems: list[str] = []
    try:
        package = load_json("package.json")
        deps = {
            **(package.get("dependencies") or {}),
            **(package.get("devDependencies") or {}),
        }
        for name in ("oxfmt", "oxlint", "typescript"):
            if name not in deps:
                problems.append(f"package.json does not declare {name}")

        if not stable_typescript_declared(deps):
            problems.append("package.json must declare stable TypeScript 7")

        for relative in ("templates/zed/settings.json", ".zed/settings.json"):
            check_zed(relative, problems)
        for relative in ("templates/vscode/settings.json", ".vscode/settings.json"):
            check_vscode(relative, problems)
        for relative in ("templates/vscode/extensions.json", ".vscode/extensions.json"):
            check_extensions(relative, problems)
        check_active_retired_references(problems)

    except (OSError, ValueError, json.JSONDecodeError) as error:
        problems.append(str(error))

    if problems:
        print("\n".join(f"ERROR: {problem}" for problem in problems))
        return 1
    print("TypeScript 7/Oxc/Zed policy OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
