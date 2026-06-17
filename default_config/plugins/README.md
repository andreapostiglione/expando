# Expando plugins

Drop Python files here to extend Expando.

## Hooks

| Function | When |
|----------|------|
| `before_expand(context)` | Before rendering a matched snippet |
| `after_expand(context)` | After expansion (`context["replacement"]` set) |
| `transform_replacement(text, context)` | Mutate rendered text before injection |
| `run(context)` | Script variable backend (`type: script`) |

`context` keys: `trigger`, `app_name`, `bundle_id`, `window_title`, `form`, `config_dir`.

## Script variable example

```yaml
vars:
  - name: tag
    type: script
    params:
      path: example.py
```

Reload plugins with `expando restart` or menu bar **Restart**.