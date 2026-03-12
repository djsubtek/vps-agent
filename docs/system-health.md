# System Health Check

This health check performs basic runtime checks for the vps-agent repository.

What it does:
- Verifies git repository status (clean / dirty)
- Reports disk usage (root filesystem)
- Reports basic memory stats via /proc/meminfo
- Prints the Python version used to run the check
- Tests TCP connectivity to api.openai.com:443

How to run:

Execute the script with Python 3 from the repository root:

python3 tools/health/health_check.py

Unit tests:

Run the tests with pytest from the repository root:

pytest -q
