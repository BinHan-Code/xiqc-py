# xiqc-py

Python library and CLI for the [ExtremeCloud IQ Controller (XIQ-C)](https://documentation.extremenetworks.com/ExtremeCloud%20IQ%20Controller%20v10.18.01%20API/index_gateway_api.html) REST API.

Pull AP / station / site inventory, feed telemetry pipelines, and script operational tasks against XIQ-C.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
# From PyPI (once published)
pip install xiqc

# From source
git clone https://github.com/BinHan-Code/xiqc-py.git
cd xiqc-py
uv sync
```

## Configuration

All settings are read from environment variables. Copy `.env.example` to `.env` and fill in your values (`.env` is gitignored).

| Variable       | Required | Default | Description                              |
|----------------|----------|---------|------------------------------------------|
| `XIQC_HOST`    | yes      | —       | Controller hostname or IP                |
| `XIQC_USER`    | yes      | —       | Admin username                           |
| `XIQC_PASS`    | yes      | —       | Admin password                           |
| `XIQC_PORT`    | no       | `5825`  | API port                                 |
| `XIQC_VERIFY`  | no       | `true`  | TLS verification. Set `false` for lab    |
| `XIQC_TIMEOUT` | no       | `30`    | Request timeout (seconds)                |

```bash
export XIQC_HOST=192.168.1.100
export XIQC_USER=admin
export XIQC_PASS=your-password
```

## CLI

```bash
# APs
xiqc aps list
xiqc aps list --format json
xiqc aps report --serial <serial>
xiqc aps smartrf --serial <serial>

# Stations (Wi-Fi clients)
xiqc stations list
xiqc stations list --no-active --duration 3D   # historical, last 3 days

# Sites
xiqc sites list
xiqc sites list --format json
xiqc sites smartrf --id <site-uuid>
```

All commands accept `--format table` (default) or `--format json`.

## Library

```python
from xiqc import XiqcClient

client = XiqcClient(
    host="192.168.1.100",
    user_id="admin",
    password="your-password",
    verify=False,  # lab only
)

# List all APs
aps = client.list_aps()
for ap in aps:
    print(ap.serial_number, ap.ap_name, ap.host_site)

# Get a single AP
ap = client.get_ap("AP-SERIAL-001")

# Per-AP RF statistics
stats = client.list_ap_stats()

# Stations
stations = client.list_stations(active=True, duration="3H")

# Sites
sites = client.list_sites()

# SmartRF
ap_rf = client.get_ap_smartrf("AP-SERIAL-001")
site_rf = client.get_site_smartrf("site-uuid")
```

All methods return typed [pydantic](https://docs.pydantic.dev/) models. See `src/xiqc/models.py` for field definitions.

## Development

```bash
uv sync                       # install all dependencies
uv run pre-commit install     # install git hooks (ruff, mypy, gitleaks)

uv run pytest                 # unit tests (no controller needed)
uv run pytest --cov=xiqc      # with coverage
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy src/              # type check
```

### Integration tests

Requires a live controller:

```bash
export XIQC_HOST=192.168.1.100
export XIQC_USER=admin
export XIQC_PASS=your-password
export XIQC_VERIFY=false      # if using self-signed cert

uv run python -m pytest -m integration -v
```

Tests auto-skip if `XIQC_HOST` is not set.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
