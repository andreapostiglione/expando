# Plugin API (v2.0)

Plugins live in:

```
~/Library/Application Support/expando/plugins/
```

Each `.py` file is loaded at startup and on config reload.

## Hooks

```python
def before_expand(context: dict) -> None: ...
def after_expand(context: dict) -> None: ...
def transform_replacement(text: str, context: dict) -> str: ...
def run(context: dict) -> str: ...  # script variables only
```

## Script variables

```yaml
matches:
  - trigger: ":where"
    replace: "App: {{app}}"
    vars:
      - name: app
        type: script
        params:
          path: my_script.py
```

Scripts must stay inside `plugins/` and define `run(context) -> str`.

## CLI

```bash
expando plugins list
```

See `default_config/plugins/example.py` for a starter template.