# SOPS Secrets Update for Ansible

**What this does**: Update SOPS-encrypted secrets files from Ansible playbooks without manually editing them. Wraps `sops set`/`sops unset` commands into a reusable task with proper error handling.

## The Problem

SOPS encrypts secrets in git, and the `community.sops` vars plugin decrypts them automatically. But there is currently no way I know of to update SOPS encrypted secrets from vars.

This task demonstrates how to solve this.

## Quick Start

Copy `tasks/update_sops_secrets.yml` to your project:

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

## Parameters

- `update_condition` (bool): When `true`, update runs
- `secrets_to_update` (dict): Key-value pairs to update. Values are interpreted as:
  - Non-empty strings: Set/update the key
  - Empty strings (`""`): Remove the key from the file
  - `null`/`~`: Ignored (no action taken)
- `secrets_file` (optional): Path to SOPS file. Defaults to auto-detected path:
  - If playbook is in a `playbooks/` directory: `../inventory/host_vars/{{ inventory_hostname }}/secrets.sops.yaml`
  - Otherwise: `inventory/host_vars/{{ inventory_hostname }}/secrets.sops.yaml`
  - Override by setting `secrets_file` explicitly
- `debug_sops` (optional): Enable debug output

## Prerequisites

- SOPS v3.11.0+ installed (`brew install sops` or see [SOPS installation](https://github.com/getsops/sops))
- Age keyfile or YubiKey configured
- Ansible configured with SOPS vars plugin (see `ansible.cfg.example`) - requires `community.sops` collection

## Setup

1. **Install SOPS and Age** (see [SOPS installation](https://github.com/getsops/sops) and [Age installation](https://github.com/FiloSottile/age))
2. **Generate age key**: `age-keygen -o ~/.config/sops/age/keys.txt`
3. **Configure SOPS**: Copy `.sops.yaml.example` to `.sops.yaml` and add your age public key
4. **Configure Ansible**: Copy `ansible.cfg.example` to `ansible.cfg` and install `community.sops` collection: `ansible-galaxy collection install -r requirements.yml`

## Local testing

**Never run `age-keygen -o ~/.config/sops/age/keys.txt`** — it will overwrite your real key and break decryption of your secrets. Use the project script instead:

```bash
./test/test_local.sh
```

This uses a project-local `.test_age_key` (gitignored) and never touches your real keyfile.

## Examples

See `examples/` directory for complete playbooks:
- `update-secrets.yml` - Basic update with provided values
- `generate-and-save.yml` - Generate secrets and save to SOPS

## Limitations

- **Updated secrets not immediately available**: Secrets updated by this task are written to disk, but won't be available in `hostvars` until the next playbook run. The SOPS vars plugin loads secrets during inventory loading (before tasks run). If you need updated values in the same run, use `community.sops.load_vars` after updating.

- **Top-level keys only**: This task supports top-level keys only. Nested key paths like `["database"]["password"]` are not supported. If you need nested keys, you would need to manage the full parent object.

- **`changed_when` detection is message-based**: The idempotency detection relies on SOPS output messages (`"already set to the same value"`, `"key not found"`). These messages may vary between SOPS versions. If you encounter issues, check your SOPS version (v3.11.0+ recommended).
