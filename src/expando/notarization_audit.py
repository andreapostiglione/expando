from __future__ import annotations

import platform
import plistlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .paths import package_root

TEAM_ID = "68Q8CQBQQV"
HARDENED_RUNTIME_FLAG = re.compile(r"runtime\b", re.IGNORECASE)


@dataclass
class NotarizationFinding:
    check_id: str
    status: str
    message: str


@dataclass
class NotarizationAuditReport:
    ok: bool
    findings: list[NotarizationFinding] = field(default_factory=list)

    def add(self, check_id: str, status: str, message: str) -> None:
        self.findings.append(NotarizationFinding(check_id=check_id, status=status, message=message))
        if status == "fail":
            self.ok = False


def expected_entitlements_path() -> Path:
    return package_root() / "scripts" / "entitlements.plist"


def load_expected_entitlements() -> dict[str, object]:
    path = expected_entitlements_path()
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        data = plistlib.load(handle)
    return data if isinstance(data, dict) else {}


def _run_command(args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _normalize_entitlements(data: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in data.items():
        if isinstance(value, list):
            normalized[key] = sorted(str(item) for item in value)
        else:
            normalized[key] = value
    return normalized


def _entitlements_match(actual: dict[str, object], expected: dict[str, object]) -> tuple[bool, str]:
    actual_norm = _normalize_entitlements(actual)
    expected_norm = _normalize_entitlements(expected)
    extra = sorted(set(actual_norm) - set(expected_norm))
    missing = sorted(set(expected_norm) - set(actual_norm))
    mismatched = [
        key
        for key in sorted(set(actual_norm) & set(expected_norm))
        if actual_norm[key] != expected_norm[key]
    ]
    if not extra and not missing and not mismatched:
        return True, "Entitlements match scripts/entitlements.plist"
    parts: list[str] = []
    if missing:
        parts.append(f"missing keys: {', '.join(missing)}")
    if extra:
        parts.append(f"unexpected keys: {', '.join(extra)}")
    if mismatched:
        parts.append(f"value mismatch: {', '.join(mismatched)}")
    return False, "; ".join(parts)


def _extract_entitlements_blob(output: str) -> dict[str, object] | None:
    text = output.strip()
    if not text:
        return None
    start = text.find("<plist")
    if start == -1:
        return None
    end = text.find("</plist>")
    if end == -1:
        return None
    blob = text[start : end + len("</plist>")]
    try:
        data = plistlib.loads(blob.encode("utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else {}


def _read_codesign_entitlements(target: Path) -> dict[str, object] | None:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as handle:
        entitlements_path = Path(handle.name)
    try:
        result = _run_command(
            ["codesign", "-d", "--entitlements", str(entitlements_path), str(target)]
        )
        if result.returncode != 0 or not entitlements_path.exists():
            combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
            return _extract_entitlements_blob(combined)
        if entitlements_path.stat().st_size == 0:
            return {}
        try:
            with entitlements_path.open("rb") as handle:
                data = plistlib.load(handle)
        except Exception:
            combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
            return _extract_entitlements_blob(combined)
        return data if isinstance(data, dict) else {}
    finally:
        entitlements_path.unlink(missing_ok=True)


def _resolve_entitlements_target(app_bundle: Path) -> Path:
    candidates = [
        app_bundle,
        app_bundle / "Contents" / "MacOS" / "expando",
        app_bundle / "Contents" / "MacOS" / "expando-sparkle",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        entitlements = _read_codesign_entitlements(candidate)
        if entitlements is not None:
            return candidate
    return app_bundle


def _codesign_details(target: Path) -> str:
    result = _run_command(["codesign", "-dvvv", str(target)])
    return "\n".join(part for part in (result.stdout, result.stderr) if part).strip()


def resolve_audit_targets(
    *,
    app_bundle: Path | None = None,
    dmg: Path | None = None,
) -> tuple[Path | None, Path | None]:
    if app_bundle is None:
        candidates = [
            package_root() / "Expando.app",
            Path("/Applications/Expando.app"),
        ]
        for candidate in candidates:
            if candidate.exists():
                app_bundle = candidate
                break
    if dmg is None:
        candidate = package_root() / "Expando.dmg"
        if candidate.exists():
            dmg = candidate
    return app_bundle, dmg


def audit_app_bundle(app_bundle: Path, *, expected: dict[str, object]) -> list[NotarizationFinding]:
    findings: list[NotarizationFinding] = []
    executable = app_bundle / "Contents" / "MacOS" / "expando"
    if not executable.exists():
        findings.append(
            NotarizationFinding(
                check_id="app.executable",
                status="fail",
                message=f"Missing main executable: {executable}",
            )
        )
        return findings

    verify = _run_command(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app_bundle)])
    if verify.returncode == 0:
        findings.append(
            NotarizationFinding(
                check_id="codesign.verify",
                status="pass",
                message="Deep codesign verification succeeded",
            )
        )
    else:
        details = (verify.stderr or verify.stdout or "codesign verify failed").strip()
        findings.append(
            NotarizationFinding(
                check_id="codesign.verify",
                status="fail",
                message=details.splitlines()[-1] if details else "codesign verify failed",
            )
        )

    details = _codesign_details(app_bundle)
    if HARDENED_RUNTIME_FLAG.search(details):
        findings.append(
            NotarizationFinding(
                check_id="codesign.hardened_runtime",
                status="pass",
                message="Hardened runtime flag present",
            )
        )
    else:
        findings.append(
            NotarizationFinding(
                check_id="codesign.hardened_runtime",
                status="fail",
                message="Hardened runtime flag missing",
            )
        )

    if TEAM_ID in details:
        findings.append(
            NotarizationFinding(
                check_id="codesign.team_id",
                status="pass",
                message=f"Developer Team ID {TEAM_ID} found in signature",
            )
        )
    else:
        findings.append(
            NotarizationFinding(
                check_id="codesign.team_id",
                status="warn",
                message=f"Team ID {TEAM_ID} not found in signature metadata",
            )
        )

    actual: dict[str, object] | None = None
    entitlements_target = app_bundle
    for candidate in (
        app_bundle / "Contents" / "MacOS" / "expando-sparkle",
        app_bundle,
        app_bundle / "Contents" / "MacOS" / "expando",
    ):
        if not candidate.exists():
            continue
        candidate_entitlements = _read_codesign_entitlements(candidate)
        if candidate_entitlements is None:
            continue
        if candidate_entitlements or not expected:
            actual = candidate_entitlements
            entitlements_target = candidate
            break

    if actual is None:
        findings.append(
            NotarizationFinding(
                check_id="entitlements.read",
                status="warn",
                message=(
                    f"Could not read entitlements from Mach-O binaries in {app_bundle.name}; "
                    "verify scripts/entitlements.plist on the signed app bundle"
                ),
            )
        )
    elif expected:
        ok, message = _entitlements_match(actual, expected)
        if not ok and actual == {}:
            findings.append(
                NotarizationFinding(
                    check_id="entitlements.baseline",
                    status="warn",
                    message=(
                        "No entitlements embedded on signed Mach-O binaries; "
                        "outer app signature carries Apple Events entitlement"
                    ),
                )
            )
        else:
            findings.append(
                NotarizationFinding(
                    check_id="entitlements.baseline",
                    status="pass" if ok else "fail",
                    message=f"{message} ({entitlements_target.name})",
                )
            )

    assess = _run_command(["spctl", "-a", "-vv", str(app_bundle)])
    output = "\n".join(part for part in (assess.stdout, assess.stderr) if part).strip()
    if assess.returncode == 0 and "accepted" in output.lower():
        findings.append(
            NotarizationFinding(
                check_id="gatekeeper.assess",
                status="pass",
                message="Gatekeeper assessment accepted",
            )
        )
    else:
        line = output.splitlines()[-1] if output else "Gatekeeper assessment failed"
        findings.append(
            NotarizationFinding(
                check_id="gatekeeper.assess",
                status="fail",
                message=line,
            )
        )

    sparkle_helper = app_bundle / "Contents" / "MacOS" / "expando-sparkle"
    sparkle_framework = app_bundle / "Contents" / "Frameworks" / "Sparkle.framework"
    if sparkle_helper.exists() or sparkle_framework.exists():
        if sparkle_helper.exists() and sparkle_framework.exists():
            findings.append(
                NotarizationFinding(
                    check_id="sparkle.embedded",
                    status="pass",
                    message="Sparkle helper and framework present",
                )
            )
        else:
            findings.append(
                NotarizationFinding(
                    check_id="sparkle.embedded",
                    status="warn",
                    message="Partial Sparkle embed (helper or framework missing)",
                )
            )
    return findings


def audit_dmg(dmg: Path) -> list[NotarizationFinding]:
    findings: list[NotarizationFinding] = []
    validate = _run_command(["xcrun", "stapler", "validate", str(dmg)])
    output = "\n".join(part for part in (validate.stdout, validate.stderr) if part).strip()
    if validate.returncode == 0:
        findings.append(
            NotarizationFinding(
                check_id="notary.staple",
                status="pass",
                message="DMG stapler validation succeeded",
            )
        )
    else:
        line = output.splitlines()[-1] if output else "stapler validate failed"
        findings.append(
            NotarizationFinding(
                check_id="notary.staple",
                status="fail",
                message=line,
            )
        )
    return findings


def run_notarization_audit(
    *,
    app_bundle: Path | None = None,
    dmg: Path | None = None,
    strict: bool = False,
) -> NotarizationAuditReport:
    report = NotarizationAuditReport(ok=True)
    if platform.system() != "Darwin":
        report.add("platform", "warn", "Notarization audit is only available on macOS")
        if strict:
            report.ok = False
        return report

    app_bundle, dmg = resolve_audit_targets(app_bundle=app_bundle, dmg=dmg)
    expected = load_expected_entitlements()

    if app_bundle is None and dmg is None:
        report.add(
            "targets",
            "warn",
            "No Expando.app or Expando.dmg found — build distribution artifacts first",
        )
        if strict:
            report.ok = False
        return report

    if app_bundle is not None:
        if not app_bundle.exists():
            report.add("app.bundle", "fail", f"App bundle not found: {app_bundle}")
        else:
            for finding in audit_app_bundle(app_bundle, expected=expected):
                report.findings.append(finding)
                if finding.status == "fail":
                    report.ok = False

    if dmg is not None:
        if not dmg.exists():
            report.add("dmg.file", "fail", f"DMG not found: {dmg}")
        else:
            for finding in audit_dmg(dmg):
                report.findings.append(finding)
                if finding.status == "fail":
                    report.ok = False

    return report


def format_notarization_audit_report(report: NotarizationAuditReport) -> str:
    from .i18n import t

    status_icon = {"pass": "✓", "warn": "!", "fail": "✗"}
    title = t("notarize.title.ok") if report.ok else t("notarize.title.issues")
    lines = [title]
    for item in report.findings:
        icon = status_icon.get(item.status, "?")
        lines.append(f"  [{icon}] {item.check_id}: {item.message}")
    return "\n".join(lines)