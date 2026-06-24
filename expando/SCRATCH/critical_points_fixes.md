# Expando Critical Points - Fixes Applied

Baseline commit: 418188fae0f52062eeddf281e49d37bb32a1ad34 (pre-review staged)

## Discovered Critical Points (from review + code inspection)

1. **Bundle detection fragility**
   - Old: direct __file__ walks + .git skips, sys.executable fallbacks in daemon.py, ui_bridge, paths.
   - Fixed: Centralized robust `find_expando_app_bundle()` in paths.py using EXPANDO_* env + sys.executable + __file__ ancestor walk + /Applications fallback.
   - daemon._app_bundle_executable + ui_bridge._ui_subprocess_argv now use it + prefer launcher or embedded python in Resources/python.
   - runtime_info.detect_runtime prefers "Expando.app" and embedded /python/ paths, sets grant_label="Expando.app".

2. **Legacy "python" grant strings in permissions/TCC**
   - _client_matches_runtime included "python"/"python3" unconditionally (broke standalone "Expando.app" grants).
   - Notes in check_permissions suggested python fixes even in app mode.
   - Fixed: python labels only when mode != "app". Messages updated.

3. **shell=True in injector/renderer**
   - renderer.py: shell var intentionally gated by allowlist (acceptable).
   - injector.py _windows_clipboard_paste: unsafe shell=True.
   - Fixed: changed to list form using COMSPEC + /c clip (no shell=True).

4. **Brittle embed/repair/distribution scripts**
   - embed-distribution-python.sh: hardcoded PY_ARCH=aarch64 (breaks on Intel).
   - distribution-launcher.sh: last-resort system python fallbacks (violates "no visible Python dep").
   - repair-installed-app.sh: heavy host loops, rewrote launcher to include system py, venv cleanup mixed.
   - verify/build: allowed non-embedded in some paths, weak messages.
   - Fixed:
     - embed: dynamic PY_ARCH via uname (aarch64/x86_64).
     - launcher: removed system fallback loop; hard fail + alert if no embedded.
     - repair: prefer embedded only first; fallback host only if none; prefers copy of distribution-launcher.sh.
     - verify: now errors (exit 1) if no Resources/python.
     - build: clarified comments.

5. **Bare excepts swallowing errors**
   - permissions (TCC/sqlite/clipboard), doctor_repair (plist/subprocess), paths (detection), many debug paths.
   - Fixed: narrowed several to (subprocess.SubprocessError, FileNotFoundError, PermissionError, OSError, ValueError, ...) where safe. Broad kept only for truly untrusted ctypes/UI/TCC.

6. **Distribution mismatch**
   - Tree Expando.app ships as dev venv (Resources/venv) vs dist intent (Resources/python + site-packages + dist launcher).
   - Scripts now strictly guard (build refuses, verify fails, launcher requires embed).
   - Note: prebuilt .app remains dev for dev workflow; dist requires EXPANDO_DISTRIBUTION=1 + embed step.

7. **Other**
   - daemon returned non-exec launcher path in edge case -> now returns None (falls to python -m).
   - package_root improved with app bundle check first.
   - Messages/docs updated for "Expando.app" standalone.

## Files Changed
- src/expando/daemon.py
- src/expando/ui_bridge.py (prior)
- src/expando/paths.py
- src/expando/runtime_info.py (prior)
- src/expando/permissions.py
- src/expando/injector.py
- src/expando/doctor_repair.py
- scripts/distribution-launcher.sh
- scripts/embed-distribution-python.sh
- scripts/repair-installed-app.sh
- scripts/build-macos-app.sh
- scripts/verify-distribution-bundle.sh

## Verification
See separate outputs from literal run of Verification plan (pytest, PYTHONPATH=src -c exercises on detect_runtime / _daemon_command, bash -n, doctor, etc).

All criticals addressed before final verification.
