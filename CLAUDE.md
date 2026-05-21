# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Keep it concise, scannable, and current. Update it when conventions change.

---

## What this project is

A Python library and CLI for the **ExtremeCloud IQ Controller (XIQ-C) REST API**.
Maintained by Bin Han (Senior Systems Engineer, Extreme Networks).

Primary use cases, in order:

1. Pull AP / Station / Site / Switch inventory and reports for dashboarding.
2. Feed a downstream telemetry pipeline (Telegraf → InfluxDB → Grafana).
3. Provide structured Wi-Fi RF data for ML anomaly-detection experiments.
4. General operational scripting against XIQ-C.

**License:** Apache 2.0. **Visibility:** public. Treat all changes as if a community contributor will read them.

---

## Stack — non-negotiable choices

These decisions are made. Do not suggest swapping unless there's a hard blocker.

| Concern        | Choice                          | Why                                                          |
|----------------|---------------------------------|--------------------------------------------------------------|
| Packaging      | `uv` + `pyproject.toml`         | Fast, lockfile-based, single tool                            |
| HTTP           | `httpx`                         | Response hooks for token refresh; async-ready                |
| Models         | `pydantic` v2                   | Validation + serialisation; every API response gets a model  |
| CLI            | `typer`                         | Type-driven, matches the API verb structure                  |
| Tests          | `pytest` + `respx`              | No live controller in CI                                     |
| Lint / format  | `ruff`                          | Replaces black + isort + flake8                              |
| Types          | `mypy --strict` on new code     | Catches integration bugs early                               |
| Git hooks      | `pre-commit` (ruff, mypy, gitleaks) | Catches issues before commit                             |

---

## Architecture rules

These are the project's spine. Violations make the codebase fragile.

1. **All HTTP goes through `XiqcClient`.** Never call `httpx` directly from CLI commands, scripts, or notebooks. If `XiqcClient` doesn't expose what you need, add a method.
2. **All auth goes through `AuthClient`.** Tokens are never passed inline, logged, or printed. `AuthClient` owns refresh logic. If you find yourself writing `Authorization: Bearer ...` outside `auth.py`, stop and use `AuthClient`.
3. **All API responses parse into pydantic models.** Even if the model only declares one field. Raw `dict` returns are not allowed in the public API.
4. **CLI commands are thin.** They parse args, call `XiqcClient`, format output. No business logic in `cli.py`.
5. **Errors are typed.** `XiqcAuthError`, `XiqcAPIError`, `XiqcConnectionError` — defined in `exceptions.py`. CLI catches these and maps to exit codes.

---

## XIQ-C API facts to remember

These are easy to forget and break things subtly.

- **Base URL:** `https://{controller}:5825/management/v1` — port `5825`, path prefix `/management/v1`.
- **Auth endpoint:** `POST /management/v1/oauth2/token` with JSON body
  `{"grantType": "password", "userId": "...", "password": "...", "scope": "..."}`.
- **Token lifetime:** `expires_in` is `7200` seconds (2 hours). Refresh proactively when under **300 seconds** remain.
- **Refresh endpoint is different from the token endpoint:**
  `POST /management/v1/oauth2/refreshToken` (not `/oauth2/token`).
  Body: `{"grantType": "refresh_token", "refreshToken": "..."}`.
  `AuthClient` handles this — see `_TOKEN_PATH` / `_REFRESH_PATH` constants in `auth.py`.
- **TLS:** controllers commonly use self-signed certs in lab/PoC environments.
  Default to `verify=True`. Honour `XIQC_VERIFY=false` for lab use, but log a loud warning on first call. Production must use proper certs.
- **API versioning:** paths mix `/v1`, `/v2`, `/v3`, `/v4`. **Do not normalise them.** Extreme uses different versions per endpoint intentionally.
  Examples: Smart RF per-AP is `/v2/aps/{serial}/smartrf`; Smart RF per-site is `/v4/sites/{siteId}/smartrf`.
- **Deprecated paths:** `/v1/aps/adoptionrules` is deprecated; new path is `/v1/devices/adoptionrules`. Implement against the new path.
- **Rate limits:** not explicitly documented. Default to **≤ 2 requests/second per controller**. Wrap calls in a polite throttle.

---

## File layout

```
xiqc-py/
├── src/xiqc/
│   ├── __init__.py        # Package version, public exports
│   ├── auth.py            # AuthClient: OAuth2 + refresh
│   ├── client.py          # XiqcClient: high-level methods
│   ├── models.py          # pydantic response models
│   ├── exceptions.py      # XiqcError hierarchy
│   ├── cli.py             # typer app
│   └── _http.py           # internal httpx setup, retry, throttle
├── tests/
│   ├── conftest.py        # live_client fixture (session-scoped, skips if no XIQC_HOST)
│   ├── test_auth.py
│   ├── test_client.py
│   ├── test_cli.py
│   ├── test_integration.py  # live controller tests (marked integration)
│   └── fixtures/          # canned API responses (synthetic only)
├── .github/workflows/ci.yml  # not yet created
├── pyproject.toml
├── README.md
├── CLAUDE.md              # this file
├── .env.example
└── .gitignore
```

Prefer extending an existing module over creating new ones until a module exceeds ~300 lines.

---

## Code conventions

- `from __future__ import annotations` at the top of every source file.
- Type hints everywhere. New code is fully typed.
- Google-style docstrings. Public methods always have one.
- f-strings over `.format()` and `%`.
- `pathlib` over `os.path`.
- `logging` module for diagnostics in library code. **Never `print()` in library code.** CLI may print user-facing output.
- Constants in `UPPER_SNAKE_CASE` at module top.
- Private functions prefixed with `_`.
- **Async: not yet.** Keep sync. We may add an async client later — don't preempt.

---

## Test conventions

- One test file per source file. `src/xiqc/auth.py` → `tests/test_auth.py`.
- Use `respx` to mock `httpx` in unit tests. **No real network calls in `test_auth`, `test_client`, or `test_cli`.**
- Fixtures live in `tests/fixtures/`. Real-looking but fully synthetic data.
  **No real serial numbers, IPs, MAC addresses, hostnames, or customer names — ever.**
- Test naming: `test_<unit>_<scenario>_<expected>`.
  Example: `test_auth_expired_token_triggers_refresh`.
- Coverage target: **≥ 90 %** on `auth.py` and `client.py`. Lower acceptable on `cli.py`.

### Integration tests (`test_integration.py`)

- All live tests carry `@pytest.mark.integration` (applied via module-level `pytestmark`).
- Use the `live_client` fixture from `conftest.py` — it builds a real `XiqcClient` from
  env vars and **auto-skips** the entire test if `XIQC_HOST` is not set.
- Assert structure only (correct model type, non-empty primary key). Never assert
  specific AP names, IPs, or site names — those differ per lab environment.
- **Never write real API responses to `tests/fixtures/`** — that would leak customer data.
- SmartRF tests catch `XiqcAPIError` and call `pytest.skip()` — SmartRF may not be
  licensed on all controllers; that is not a test failure.
- Run with: `python -m pytest -m integration -v` (requires env vars set first).

---

## Security and sensitivity — strict

This repo is **public**. The maintainer works for Extreme Networks supporting Japanese government customers. The following rules are non-negotiable.

1. **No real customer data, ever.** No real IPs, hostnames, AP serials, MAC addresses, site names, or RF telemetry. Use synthetic values:
   - IPs: `10.99.0.0/16` or `192.0.2.0/24` (TEST-NET-1)
   - AP serials: `LAB-AP-0001`, `LAB-AP-0002`, …
   - MACs: `02:00:00:xx:xx:xx` (locally administered, unicast)
   - Hostnames: `lab-ap-01.example.test`
2. **No credentials in code or commits.** Use environment variables or OS keyring. `.env.example` shows variable names only.
3. **No internal Extreme proprietary information.** No internal URLs, unreleased product names, unreleased API versions, or internal tooling references.
4. **Logs must redact secrets.** `AuthClient` never logs token values; use `<redacted>` placeholders.
5. **Pre-commit runs `gitleaks`** to scan for accidentally committed secrets. Do not bypass.
6. **If unsure whether something is sensitive, ask before committing.** A 30-second check beats a force-push-with-rewrite.

---

## Common commands

```bash
# Setup (preferred — uv)
uv sync                          # install deps from lockfile
uv run pre-commit install        # install git hooks

# Setup (fallback — plain pip)
pip install -e ".[dev]"          # if uv is not installed

# Development
uv run pytest                    # run all tests (unit; integration skipped unless XIQC_HOST set)
uv run pytest -k auth            # run a subset by keyword
uv run pytest --cov=xiqc         # with coverage
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy src/                 # type check

# Without uv
python -m pytest
python -m pytest -k auth

# Integration tests against a real controller (PowerShell)
$env:XIQC_HOST="192.168.x.x"; $env:XIQC_USER="admin"; $env:XIQC_PASS="..."; $env:XIQC_VERIFY="false"
python -m pytest -m integration -v    # live tests only
python -m pytest -v                   # unit + live together

# CLI usage (after install)
xiqc aps list
xiqc aps list --format json
xiqc aps report --serial <serial>
xiqc aps stats
xiqc aps stats --format json
xiqc aps smartrf --serial <serial>
xiqc stations list
xiqc stations list --no-active --duration 3D
xiqc sites list
xiqc sites smartrf --id <uuid>

# Build
uv build                         # build wheel + sdist
```

---

## Environment variables

Read from environment only — never from config files in the repo.

| Variable       | Required | Default      | Purpose                                              |
|----------------|----------|--------------|------------------------------------------------------|
| `XIQC_HOST`    | yes      | —            | Controller hostname or IP                            |
| `XIQC_USER`    | yes      | —            | Admin username                                        |
| `XIQC_PASS`    | yes      | —            | Admin password                                        |
| `XIQC_PORT`    | no       | `5825`       | API port                                              |
| `XIQC_VERIFY`  | no       | `true`       | TLS verification. Set `false` only in lab            |
| `XIQC_TIMEOUT` | no       | `30`         | Request timeout (seconds)                             |
| `XIQC_SCOPE`   | no       | empty        | OAuth2 scope                                          |

`.env` is gitignored. `.env.example` shows variable names only, never values.

---

## Versioning and releases

- **SemVer**: `MAJOR.MINOR.PATCH`.
- Pre-1.0: breaking changes can land in `MINOR`. Document them in `CHANGELOG.md`.
- Tag releases: `git tag v0.1.0 && git push --tags`.
- PyPI publish (later): `uv publish`. Not yet automated.

---

## What to ask before doing

These actions need a human decision, not an autonomous one:

- Adding a new top-level dependency to `pyproject.toml`.
- Changing the public API surface (renaming methods, changing signatures).
- Adding a new module to the package.
- Touching `auth.py` beyond bug fixes.
- Modifying CI workflows.
- Anything tagged `TODO: design` in code.

For everything else, proceed and show a diff.

---

## Anti-patterns to avoid

- Catching `Exception` broadly. Catch specific exceptions and re-raise as typed errors.
- Adding "helpful" defaults that mask configuration mistakes (e.g., silently falling back to insecure TLS).
- Inline strings for API paths. Define them as module constants in `client.py`.
- Mixing CLI output formatting with library logic.
- Importing from private modules (`xiqc._http`) from outside the package.
- Adding loops over many APs/sites without rate-limiting or batching.

---

## pyxccsdk — official reference (dev-only, not a runtime dep)

`pyxccsdk` is Extreme Networks' own Python SDK for XIQ-C (TestPyPI: `pyxccsdk`).
It is installed as a **dev-only** reference tool — **never add it to `[project.dependencies]`** (TestPyPI, pre-release, uses `requests` not `httpx`).

Use it to discover endpoint URLs, request shapes, and response field names. The `xcc.api.Client.rest` dict in its source is the authoritative endpoint map. Key findings already extracted:
- Stations are queried via `GET management/v1/stations/query` (params: `showActive`, `duration`).
- Reports use `GET management/v3/sites/report/flex` — returns base64+zlib-compressed frames.
- API versions are intentionally mixed: `/v1`, `/v2`, `/v3`, `/v4` — never normalise.
- AP primary key: `serialNumber`. Station primary key: `macAddress`. Site primary key: `id` (UUID).
- `/v1/aps/query` returns **camelCase** field names (`serialNumber`, `hardwareType`, `ipAddress`,
  `snr`, etc.) — not PascalCase. The `ApStats` model aliases reflect the real response shape.
- `Site.features` is a `list[str]` (e.g. `["CENTRALIZED-SITE"]`), not a dict.
- `Radio.txBf` is returned as a string (`"enabled"`/`"disabled"`), not a boolean — the model
  validator in `Radio` coerces it.

---

## Useful references

- ExtremeCloud IQ Controller REST API Gateway:
  <https://documentation.extremenetworks.com/ExtremeCloud%20IQ%20Controller%20v10.18.01%20API/index_gateway_api.html>
- Platform Manager API:
  <https://documentation.extremenetworks.com/ExtremeCloud%20IQ%20Controller%20v10.18.01%20API/index_platform_manager.html>
- Apps Manager API:
  <https://documentation.extremenetworks.com/ExtremeCloud%20IQ%20Controller%20v10.18.01%20API/index_apps_manager.html>
- httpx: <https://www.python-httpx.org/>
- pydantic v2: <https://docs.pydantic.dev/latest/>
- typer: <https://typer.tiangolo.com/>
- uv: <https://docs.astral.sh/uv/>
- respx: <https://lundberg.github.io/respx/>
