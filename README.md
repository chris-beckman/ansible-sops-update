# SOPS Secrets Update for Ansible

**What this does**: Update SOPS-encrypted secrets files from Ansible playbooks without manually editing them. Wraps `sops set`/`sops unset` with proper error handling.

## The Problem

SOPS encrypts secrets in git, and the `community.sops` vars plugin decrypts them automatically. There is no built-in way to update SOPS-encrypted secrets from Ansible vars. This task fills that gap.

## Quick Start

Copy `tasks/` and `filter_plugins/` to your project, then:

```yaml
- name: Update secrets in SOPS file
  include_tasks: tasks/update_sops_secrets.yml
  vars:
    update_condition: true
    secrets_to_update:
      api_token: "new-token-value-12345"
      old_key: ""  # Empty string removes the key
```

## Usage

### Update with values you have
```yaml
- name: Update secrets
  include_tasks: tasks/update_sops_secrets.yml
  vars:
    update_condition: true
    secrets_to_update:
      api_token: "{{ provided_token }}"
```

### Generate and save
```yaml
- name: Generate password
  ansible.builtin.command:
    cmd: openssl rand -base64 32
  register: password_result

- name: Save to SOPS
  include_tasks: tasks/update_sops_secrets.yml
  vars:
    update_condition: true
    secrets_to_update:
      database_password: "{{ password_result.stdout }}"
```

### List values
```yaml
- name: Update secrets including a list
  include_tasks: tasks/update_sops_secrets.yml
  vars:
    update_condition: true
    secrets_to_update:
      allowed_ips: ["10.0.0.1", "10.0.0.2"]
```

## Parameters

- `update_condition` (bool): When `true`, update runs
- `secrets_to_update` (dict): Key-value pairs. Empty strings remove keys. Supports scalars and lists.
- `secrets_scope` (optional): `host` (default) or `global`. Host: `host_vars/{{ inventory_hostname }}/secrets.sops.yaml`; global: `group_vars/all/secrets.sops.yaml`
- `secrets_file` (optional): Override path to SOPS file
- `sops_age_keyfile` (optional): Path to age keyfile. Defaults to `SOPS_AGE_KEY_FILE` env or `~/.config/sops/age/keys.txt`
- `debug_sops` (optional): Enable debug output

Path resolution uses `inventory_dir` when available (from `-i inventory/` or `-i inventory/hosts.ini`), else `playbook_dir/../inventory`. Use `secrets_file` to override.

## Prerequisites

- SOPS v3.11.0+
- Age keyfile or YubiKey
- Ansible with `community.sops` collection

## Setup

1. Install SOPS and Age
2. Generate age key: `age-keygen -o ~/.config/sops/age/keys.txt`
3. Copy `.sops.yaml.example` to `.sops.yaml` and add your age public key
4. Copy `ansible.cfg.example` to `ansible.cfg`, set `filter_plugins = filter_plugins`, install `community.sops`: `ansible-galaxy collection install -r requirements.yml`

## Examples

- `examples/update-secrets.yml` - Basic update
- `examples/generate-and-save.yml` - Generate and save

Run examples from the repository root, e.g.:

```bash
ansible-playbook -i inventory/hosts.ini examples/update-secrets.yml -e "inventory_hostname=your-host"
```

## Limitations

- Updated secrets are not available in `hostvars` until the next playbook run. Use `community.sops.load_vars` after updating if you need them in the same run.
