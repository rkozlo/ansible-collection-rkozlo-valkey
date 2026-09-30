# valkey

Ansible collection for managing Valkey users, executing raw Valkey commands, and gathering Valkey server information.

## Requirements

- Ansible >= 2.18
- Python >= 3.13
- Valkey server >= 7.2 <= 9.1
- Python library valkey>=6.1.1,<7.0.0


## Installation

```bash
ansible-galaxy collection install rkozlo.valkey
```

## Modules

- `rkozlo.valkey.valkey_user` — manage Valkey users, passwords, commands, categories, key patterns, and channels.
- `rkozlo.valkey.valkey_exec` — execute arbitrary Valkey commands for advanced use cases.
- `rkozlo.valkey.valkey_info` — retrieve Valkey server information and status.
- `rkozlo.valkey.valkey_wait` — wait until Valkey will be in certain condition.
- `rkozlo.valkey.valkey_config` - change server configs.

## Examples

### Create or update a Valkey user

```yaml
- name: Ensure Valkey user exists
  rkozlo.valkey.valkey_user:
    login_host: localhost
    login_port: 6379
    name: alice
    passwords:
      - secret
    enabled: true
    commands:
      - +get
      - +set
    key_patterns:
      - ~user:* 
```

### Execute a raw Valkey command

```yaml
- name: Execute GET command
  rkozlo.valkey.valkey_exec:
    login_host: localhost
    login_port: 6379
    command: GET
    args:
      - mykey
```

### Gather Valkey server info

```yaml
- name: Retrieve server and memory info
  rkozlo.valkey.valkey_info:
    login_host: localhost
    login_port: 6379
    sections:
      - server
      - memory
```

### Change server configs

```yaml
- name: Change server configs
  rkozlo.valkey.valkey_config:
    configs:
      maxmemory: 100000
      maxmemory-policy: volatile-ttl
      save: 60 60
      client-output-buffer-limit: "normal 1 1 1 slave 268435456 67108864 60 pubsub 33554432 8388608 60"
```

## Notes

- `valkey_exec` is intended for advanced users and executes the command directly through the Valkey client.
- `valkey_exec` does not attempt to determine whether a command changed server state.
- `valkey_user` supports append and reset modes, but some parameter combinations may require careful review of module behavior.
- `valkey_config` will change mutable configs. If passed config is immutable and is different warning will appear(or fail if strict mode enabled)
- The collection is under active development and may be updated after initial release.

## Testing

- Unit tests are available under `tests/unit/`
- Integration tests are available under `tests/integration/`
- GitHub Actions run sanity, unit, and integration checks using the repository test matrix.

## Author

Rafał Kozłowski <rafalkozlowski07@gmail.com>

## License

GPL-3.0-or-later
