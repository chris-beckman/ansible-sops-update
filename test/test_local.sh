#!/usr/bin/env bash
# Run tests locally using a project-local age key. Never touches ~/.config/sops/age/keys.txt.
set -euo pipefail
cd "$(dirname "$0")/.."
KEYFILE="$(pwd)/.test_age_key"
CFG_BAK=""
trap 'rm -f "$KEYFILE"; [ -n "$CFG_BAK" ] && mv "$CFG_BAK" ansible.cfg' EXIT
rm -f "$KEYFILE"
age-keygen -o "$KEYFILE"
chmod 600 "$KEYFILE"
export SOPS_AGE_KEY_FILE="$KEYFILE"
AGE_PUB=$(age-keygen -y "$KEYFILE")
mkdir -p test_inventory/host_vars/test-host
sed -e "s|- age1.*|- $AGE_PUB|" -e "s|inventory/|test_inventory/|" .sops.yaml.example > .sops.yaml
cat > test_inventory/host_vars/test-host/secrets.sops.yaml <<'EOF'
api_token: "initial-token-value"
database_password: "initial-password"
old_key: "to-be-removed"
EOF
sops -e -i test_inventory/host_vars/test-host/secrets.sops.yaml
[ -f ansible.cfg ] && CFG_BAK=$(mktemp) && cp ansible.cfg "$CFG_BAK"
cat > ansible.cfg <<ANSCFG
[defaults]
inventory = test_inventory/hosts.ini
host_key_checking = False
retry_files_enabled = False
vars_plugins_enabled = host_group_vars,community.sops.sops

[community.sops]
age_keyfile = $KEYFILE

[privilege_escalation]
become = True
become_method = sudo
ANSCFG
cat > test_inventory/hosts.ini <<'EOF'
[test]
test-host ansible_connection=local
EOF
ansible-playbook -i test_inventory/hosts.ini test/test-sops-update.yml -e "sops_age_keyfile=$KEYFILE" -e "secrets_file=$(pwd)/test_inventory/host_vars/test-host/secrets.sops.yaml"
sops -d test_inventory/host_vars/test-host/secrets.sops.yaml | grep -q "api_token: new-token-12345" && echo "[OK] test passed"
