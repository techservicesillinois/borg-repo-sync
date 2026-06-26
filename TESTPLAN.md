## Automated Tests

```sh
make clean
make unit
```

## Manual Tests

### borg compare

```sh
source .venv/bin/activate
borg compare
```

### Test that borg defaults to our remote default configuration

```sh
source .venv/bin/activate
rm .borg.toml
borg --debug compare
```

Look for 'borg configured from default URL at...' in the output.

To clean up:

```sh
git checkout .borg.toml
```

### Test borg with a remote configuration

```sh
borg -d -u https://raw.githubusercontent.com/techservicesillinois/secdev-template-python/refs/heads/main/.borg.toml compare
```

Expect output to contain:

```
Fetching remote config file https://raw.githubusercontent.com/techservicesillinois/secdev-template-python/refs/heads/main/.borg.toml
```
