#!/usr/bin/env bash
# Run tests locally (mirrors CI). Requires SOPS, Age, Ansible, pytest.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Unit tests ==="
pip install -q -r requirements-dev.txt
PYTHONPATH=. pytest tests/unit/ -v

echo ""
echo "=== Integration tests ==="
echo "Run these manually after setting up test_inventory (see README):"
echo "  ansible-playbook -i test_inventory/hosts.ini test/test-sops-noop.yml"
echo "  ansible-playbook -i test_inventory/hosts.ini test/test-sops-update.yml"
echo "  ansible-playbook -i test_inventory/hosts.ini test/test-sops-list.yml"
echo "  ... (see .github/workflows/test.yml for full sequence)"
