from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from levelupdiag_core.commands import find_executable
from levelupdiag_core.config import AppConfig
from levelupdiag_core.models import Artifact, Finding, LevelResult
from levelupdiag_core.reports import read_level_result
from levelupdiag_core.verdicts import CONFIG_ERROR, FAIL, INFRA_ERROR, PASS, SKIP, WARN

from .common import (
    active_session,
    command_probe,
    command_value,
    kx_config,
    make_result,
    now,
    resolve_command,
    session_metadata,
    start_session,
    target_paths,
)
from .http_probe import probe as http_probe
from .source_audit import audit as source_audit


def _tool_candidates(name: str) -> list[str]:
    if os.name == "nt":
        return [f"{name}.exe", f"{name}.cmd", name]
    return [name]


def _find_tool(name: str) -> str | None:
    for candidate in _tool_candidates(name):
        path = find_executable(candidate)
        if path:
            return path
    if name == 'pnpm':
        return find_executable('corepack.cmd' if os.name == 'nt' else 'corepack') or find_executable('corepack')
    return None

def _sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def discovery(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started = now()
    session_id = start_session(config)
    paths = target_paths(config)
    findings: list[Finding] = []
    root = paths["root"]
    if root and root.is_dir():
        findings.append(Finding("kx.discovery.target", PASS, f"Konnaxion target found: {root}", "discovery", path=str(root)))
    else:
        findings.append(Finding("kx.discovery.target", CONFIG_ERROR, "Konnaxion target repository is missing.", "discovery", path=str(root)))

    for key in ("frontend", "backend"):
        path = paths[key]
        severity = PASS if path and path.is_dir() else CONFIG_ERROR
        findings.append(Finding(f"kx.discovery.{key}", severity, f"{key} directory {'found' if severity == PASS else 'missing'}.", "discovery", path=str(path)))

    tools = ["git", "node", "pnpm"]
    for name in tools:
        resolved = _find_tool(name)
        findings.append(Finding(
            f"kx.tool.{name}", PASS if resolved else WARN,
            f"{name} {'available' if resolved else 'not found on PATH'}.",
            "toolchain", path=resolved,
            recommendation=None if resolved else f"Install or configure {name} before running checks that require it.",
        ))
    findings.append(Finding("kx.tool.python", PASS, f"Python available: {sys.executable}", "toolchain", path=sys.executable, evidence=platform.python_version()))

    capsule_manager = paths["capsule_manager"]
    findings.append(Finding(
        "kx.discovery.capsule-manager",
        PASS if capsule_manager and capsule_manager.is_dir() else WARN,
        "Capsule Manager repository is configured and present." if capsule_manager and capsule_manager.is_dir() else "Capsule Manager repository is not configured/present; capsule diagnostics will be limited.",
        "discovery", path=str(capsule_manager) if capsule_manager else None,
    ))
    return make_result(level_id, level_name, started, findings, metadata={"diagnostic_session_id": session_id, "cwd": str(root), "python": platform.python_version(), "platform": platform.platform()})


def repository_static(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started = now(); paths = target_paths(config); root = paths["root"]; findings: list[Finding] = []
    expected = ["frontend/package.json", "backend/manage.py"]
    for rel in expected:
        path = root / rel
        findings.append(Finding(f"kx.repo.{rel.replace('/', '.').replace('_','-')}", PASS if path.is_file() else FAIL, f"Required repository surface {'present' if path.is_file() else 'missing'}: {rel}", "repository", path=str(path)))
    git_cmd = ["git", "status", "--short"]
    finding, step = command_probe(config, finding_id="kx.repo.git-status", label="Git status", command=git_cmd, cwd=root, timeout=60, optional=True)
    findings.append(finding)
    output = step.output_tail if step else ""
    return make_result(level_id, level_name, started, findings, output=output, metadata={**session_metadata(config), "cwd": str(root)})


def backend(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started = now(); backend_dir = target_paths(config)["backend"]; findings: list[Finding] = []; outputs=[]
    assert backend_dir is not None
    specs = [
        ("kx.backend.django-check", "Django system check", "backend_check", ["python", "manage.py", "check"], False, 180),
        ("kx.backend.migrations", "Django migration drift check", "backend_migrations", ["python", "manage.py", "makemigrations", "--check", "--dry-run"], False, 240),
        ("kx.backend.smoke", "Backend platform smoke tests", "backend_smoke", ["python", "-m", "pytest", "tests/test_smoke_platform.py", "-q"], False, 600),
    ]
    for fid,label,key,default,opt,timeout in specs:
        cmd = command_value(config, key) or default
        finding, step = command_probe(config, finding_id=fid, label=label, command=cmd, cwd=backend_dir, timeout=timeout, optional=opt)
        findings.append(finding)
        if step: outputs.append(f"## {label}\n{step.output_tail}")
    return make_result(level_id, level_name, started, findings, output="\n\n".join(outputs), metadata={**session_metadata(config), "cwd": str(backend_dir)})


def frontend(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started = now(); frontend_dir = target_paths(config)["frontend"]; findings: list[Finding] = []; outputs=[]
    assert frontend_dir is not None
    specs = [
        ("kx.frontend.typecheck", "TypeScript typecheck", "frontend_typecheck", ["pnpm", "exec", "tsc", "-p", "tsconfig.json", "--noEmit", "--pretty", "false"], False, 600),
        ("kx.frontend.eslint", "Frontend ESLint", "frontend_lint", ["pnpm", "exec", "eslint", ".", "--max-warnings=0"], False, 600),
        ("kx.frontend.jest", "Frontend Jest", "frontend_jest", ["pnpm", "exec", "jest", "--passWithNoTests", "--runInBand"], False, 900),
        ("kx.frontend.build", "Next production build", "frontend_build", ["pnpm", "exec", "next", "build"], False, 1200),
    ]
    for fid,label,key,default,opt,timeout in specs:
        cmd = command_value(config, key) or default
        finding, step = command_probe(config, finding_id=fid, label=label, command=cmd, cwd=frontend_dir, timeout=timeout, optional=opt)
        findings.append(finding)
        if step: outputs.append(f"## {label}\n{step.output_tail}")
    return make_result(level_id, level_name, started, findings, output="\n\n".join(outputs), metadata={**session_metadata(config), "cwd": str(frontend_dir)})


def contracts(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started = now(); paths = target_paths(config); findings=[]; outputs=[]
    specs = [
        ("kx.contract.backend-api-scan", "Django API scanner", "backend_api_scan", ["python", "django_api_scanner.py"], paths["backend"], True, 300),
        ("kx.contract.frontend-endpoints", "Frontend endpoint scan", "frontend_endpoint_scan", ["node", "scripts/scan-endpoints.mjs"], paths["frontend"], True, 300),
        ("kx.contract.openapi-tests", "OpenAPI contract tests", "backend_openapi", ["python", "-m", "pytest", "konnaxion/users/tests/api/test_openapi.py", "-q"], paths["backend"], False, 600),
    ]
    for fid,label,key,default,cwd,opt,timeout in specs:
        assert cwd is not None
        cmd = command_value(config,key) or default
        finding, step = command_probe(config, finding_id=fid, label=label, command=cmd, cwd=cwd, timeout=timeout, optional=opt)
        findings.append(finding)
        if step: outputs.append(f"## {label}\n{step.output_tail}")
    audit = source_audit(paths["frontend"], paths["backend"])
    findings.append(Finding("kx.contract.double-api", FAIL if audit["double_api"] else PASS, f"Double /api prefix: {len(audit['double_api'])}", "contract", evidence=str(audit["double_api"][:20])))
    findings.append(Finding("kx.contract.forbidden-namespaces", FAIL if audit["forbidden"] else PASS, f"Forbidden legacy API calls: {len(audit['forbidden'])}", "contract", evidence=str(audit["forbidden"][:30])))
    findings.append(Finding("kx.contract.csrf-risk", WARN if audit["csrf_risk_files"] else PASS, f"Mutation files requiring CSRF review: {len(audit['csrf_risk_files'])}", "auth", evidence=str(audit["csrf_risk_files"][:30]), recommendation="Review raw mutation fetches. Calls through apiFetch/apiPost/apiPut/apiPatch/apiDelete or services/_request are treated as CSRF-aware." if audit["csrf_risk_files"] else None))
    findings.append(Finding("kx.contract.unmapped", WARN if audit["unmapped"] else PASS, f"Frontend endpoints not mapped to discovered backend prefixes: {len(audit['unmapped'])}", "contract", evidence=str(audit["unmapped"][:40])))
    return make_result(level_id, level_name, started, findings, output="\n\n".join(outputs), metadata={**session_metadata(config), "cwd": str(paths["root"]), "source_audit": audit})



def _start_runtime_process(command: list[str] | None, cwd: Path, env: dict[str, str]) -> subprocess.Popen[str] | None:
    if not command or not cwd.is_dir():
        return None
    args = resolve_command(command, cwd=cwd)
    kwargs: dict[str, Any] = {
        "cwd": str(cwd),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
        "text": True,
        "shell": False,
    }
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(args, **kwargs)


def _stop_runtime_process(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                shell=False,
                check=False,
            )
        else:
            import signal
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        try:
            proc.kill()
        except OSError:
            pass


def _wait_for_urls(urls: list[str], timeout_seconds: int) -> dict[str, tuple[bool, str]]:
    deadline = time.monotonic() + max(1, timeout_seconds)
    pending = set(urls)
    results: dict[str, tuple[bool, str]] = {}
    last_errors: dict[str, str] = {}
    while pending and time.monotonic() < deadline:
        for url in list(pending):
            result = http_probe(url, timeout=2.0)
            if result.ok:
                results[url] = (True, f"HTTP {result.status} in {result.elapsed_ms}ms")
                pending.remove(url)
            else:
                last_errors[url] = result.error
        if pending:
            time.sleep(1.0)
    for url in pending:
        results[url] = (False, last_errors.get(url) or "startup timeout")
    return results

def runtime_smoke(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started = now()
    paths = target_paths(config)
    section = kx_config(config)
    frontend_dir = paths["frontend"] or config.target_root_path
    backend_dir = paths["backend"] or config.target_root_path
    urls = section.get("local_urls", ["http://127.0.0.1:3000", "http://127.0.0.1:8000/api/"])
    findings: list[Finding] = []
    started_processes: list[subprocess.Popen[str] | None] = []

    initial = {str(url): http_probe(str(url), timeout=3.0) for url in urls}
    needs_runtime = any(not result.ok for result in initial.values())
    autostart = bool(section.get("runtime_autostart", True))

    try:
        if needs_runtime and autostart:
            backend_cmd = command_value(config, "backend_runtime_start")
            frontend_cmd = command_value(config, "frontend_runtime_start")
            backend_needed = any(
                not result.ok and (":8000" in url or "/api" in url)
                for url, result in initial.items()
            )
            frontend_needed = any(
                not result.ok and ":3000" in url
                for url, result in initial.items()
            )
            backend_proc = _start_runtime_process(backend_cmd, backend_dir, config.env()) if backend_needed else None
            frontend_proc = _start_runtime_process(frontend_cmd, frontend_dir, config.env()) if frontend_needed else None
            started_processes.extend([backend_proc, frontend_proc])

            if backend_proc is not None:
                findings.append(Finding("kx.runtime.backend-start", PASS, "Backend runtime started by LevelUpDiag.", "runtime", path=str(backend_dir)))
            if frontend_proc is not None:
                findings.append(Finding("kx.runtime.frontend-start", PASS, "Frontend runtime started by LevelUpDiag.", "runtime", path=str(frontend_dir)))

            startup_timeout = int(section.get("runtime_startup_timeout_seconds", 120))
            readiness = _wait_for_urls([str(url) for url in urls], startup_timeout)
            for url in urls:
                ok, evidence = readiness[str(url)]
                findings.append(Finding(
                    "kx.runtime.local-http-ready",
                    PASS if ok else WARN,
                    f"Local runtime {'ready' if ok else 'not ready'}: {url}",
                    "runtime",
                    evidence=evidence,
                ))
        else:
            for url, result in initial.items():
                findings.append(Finding(
                    "kx.runtime.local-http",
                    PASS if result.ok else WARN,
                    f"Local probe {url}: {'OK' if result.ok else 'REFUSED/ERROR'}",
                    "runtime",
                    evidence=result.error or f"HTTP {result.status} {result.elapsed_ms}ms",
                ))

        seed_cmd = command_value(config, "ethikos_seed_workflow") or [
            "python",
            "manage.py",
            "seed_ethikos_workflow",
        ]
        seed_finding, _seed_step = command_probe(
            config,
            finding_id="kx.runtime.ethikos-seed",
            label="Ethikos workflow seed",
            command=seed_cmd,
            cwd=backend_dir,
            timeout=300,
            optional=True,
            recommendation=(
                "The authenticated Playwright workflow needs the canonical local "
                "Ethikos seed data."
            ),
        )
        findings.append(seed_finding)

        cmd = command_value(config, "playwright_smoke") or ["pnpm", "run", "smoke:gate"]
        finding, step = command_probe(
            config,
            finding_id="kx.runtime.playwright-smoke",
            label="Playwright smoke gate",
            command=cmd,
            cwd=frontend_dir,
            timeout=1200,
            optional=True,
            recommendation="Inspect Playwright failures and retained current-run artifacts. The smoke gate runs with SMOKE_GATE=1.",
        )
        findings.append(finding)
        return make_result(
            level_id,
            level_name,
            started,
            findings,
            output=step.output_tail if step else "",
            metadata={**session_metadata(config), "autostarted_runtime": needs_runtime and autostart},
        )
    finally:
        for proc in reversed(started_processes):
            _stop_runtime_process(proc)

def jobs(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started=now(); backend_dir=target_paths(config)["backend"]; findings=[]; outputs=[]; assert backend_dir is not None
    specs=[
        ("kx.jobs.celery-tests","Celery task tests","backend_task_tests",["python","-m","pytest","konnaxion/users/tests/test_tasks.py","-q"],True,600),
        ("kx.jobs.custom-probe","Configured Redis/Celery runtime probe","jobs_probe",None,True,300),
    ]
    for fid,label,key,default,opt,timeout in specs:
        cmd=command_value(config,key) or default
        finding,step=command_probe(config,finding_id=fid,label=label,command=cmd,cwd=backend_dir,timeout=timeout,optional=opt,recommendation="Configure konnaxion.commands.jobs_probe for live Redis/Celery verification." if key=="jobs_probe" else None)
        findings.append(finding)
        if step: outputs.append(step.output_tail)
    return make_result(level_id,level_name,started,findings,output="\n".join(outputs),metadata={**session_metadata(config),"cwd":str(backend_dir)})


def security(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started=now(); paths=target_paths(config); findings=[]; outputs=[]; backend_dir=paths["backend"]; assert backend_dir is not None
    cmd=command_value(config,"django_deploy_check") or ["python","manage.py","check","--deploy"]
    finding,step=command_probe(config,finding_id="kx.security.django-deploy-check",label="Django deploy security check",command=cmd,cwd=backend_dir,timeout=300,optional=True)
    findings.append(finding)
    if step: outputs.append(step.output_tail)
    cm=paths["capsule_manager"]
    if cm and cm.is_dir():
        cmd=command_value(config,"capsule_security_tests") or ["python","-m","pytest","tests/test_security_gate.py","-q"]
        finding,step=command_probe(config,finding_id="kx.security.capsule-gate",label="Capsule Manager security gate tests",command=cmd,cwd=cm,timeout=600,optional=True)
        findings.append(finding)
        if step: outputs.append(step.output_tail)
    else:
        findings.append(Finding("kx.security.capsule-gate",WARN,"Capsule Manager security checks unavailable because its repository is not configured.","security"))
    return make_result(level_id,level_name,started,findings,output="\n".join(outputs),metadata={**session_metadata(config),"cwd":str(paths["root"])})


def capsule_local(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started=now(); paths=target_paths(config); findings=[]; outputs=[]
    cm=paths["capsule_manager"]; capsule=paths["capsule_file"]
    if cm and cm.is_dir():
        findings.append(Finding("kx.capsule.manager-repo",PASS,"Capsule Manager repository available.","capsule",path=str(cm)))
        health=cm/"kx_agent"/"runtime"/"healthchecks.py"
        findings.append(Finding("kx.capsule.healthchecks-source",PASS if health.is_file() else WARN,"Capsule runtime healthcheck engine found." if health.is_file() else "Capsule runtime healthcheck engine not found at expected path.","capsule",path=str(health)))
        cmd=command_value(config,"capsule_manager_tests") or ["python","-m","pytest","tests/test_instance_states.py","-q"]
        finding,step=command_probe(config,finding_id="kx.capsule.manager-tests",label="Capsule Manager instance-state tests",command=cmd,cwd=cm,timeout=600,optional=True)
        findings.append(finding)
        if step: outputs.append(step.output_tail)
    else:
        findings.append(Finding("kx.capsule.manager-repo",WARN,"Capsule Manager repository not configured; local capsule diagnostics are limited.","capsule"))
    if capsule:
        if capsule.is_file():
            digest=_sha256_file(capsule)
            findings.append(Finding("kx.capsule.file",PASS,"Configured capsule file exists and was hashed.","capsule",path=str(capsule),evidence=f"sha256={digest} size={capsule.stat().st_size}"))
        else:
            findings.append(Finding("kx.capsule.file",WARN,"Configured capsule file does not exist.","capsule",path=str(capsule)))
    else:
        findings.append(Finding("kx.capsule.file",SKIP,"No capsule file configured; file integrity probe skipped.","capsule"))
    return make_result(level_id,level_name,started,findings,output="\n".join(outputs),metadata={**session_metadata(config),"cwd":str(cm or paths["root"])})


def deployed(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started=now(); section=kx_config(config); findings=[]; outputs=[]
    remote=section.get("remote", {}); remote=dict(remote) if isinstance(remote,dict) else {}
    enabled=bool(remote.get("enabled",False))
    if not enabled:
        findings.append(Finding("kx.remote.enabled",WARN,"Remote diagnostics are disabled. Local diagnostics remain active.","remote",recommendation="Set konnaxion.remote.enabled=true only when deployed-runtime diagnostics are desired."))
        return make_result(level_id,level_name,started,findings,metadata={**session_metadata(config),"remote_enabled":False})
    domain=str(remote.get("domain","")).strip()
    urls=remote.get("urls")
    if not isinstance(urls,list) or not urls:
        urls=[f"https://{domain}/",f"https://{domain}/api/",f"https://{domain}/admin/"] if domain else []
    for index,url in enumerate(urls):
        if not isinstance(url,str) or not url.strip(): continue
        result=http_probe(url,timeout=float(remote.get("http_timeout_seconds",10)),allow_insecure_tls=bool(remote.get("allow_insecure_tls",False)))
        findings.append(Finding(f"kx.remote.http.{index:02d}",PASS if result.ok else FAIL,f"Remote HTTP probe {'succeeded' if result.ok else 'failed'}: {url}","remote",path=url,evidence=f"status={result.status} elapsed_ms={result.elapsed_ms} error={result.error}"))
    if domain:
        try:
            addresses=sorted({item[4][0] for item in socket.getaddrinfo(domain,None)})
            findings.append(Finding("kx.remote.dns",PASS,f"DNS resolved for {domain}.","remote",path=domain,evidence=", ".join(addresses)))
        except OSError as exc:
            findings.append(Finding("kx.remote.dns",FAIL,f"DNS resolution failed for {domain}.","remote",path=domain,evidence=str(exc)))
    deep=command_value(config,"remote_deep_diagnostic")
    if deep:
        cwd=target_paths(config)["capsule_manager"] or config.target_root_path
        finding,step=command_probe(config,finding_id="kx.remote.deep-diagnostic",label="Configured deep deployed-runtime diagnostic",command=deep,cwd=cwd,timeout=int(remote.get("deep_timeout_seconds",1800)),optional=True)
        findings.append(finding)
        if step: outputs.append(step.output_tail)
    else:
        findings.append(Finding("kx.remote.deep-diagnostic",SKIP,"No deep remote diagnostic command configured; read-only HTTP/DNS probes only.","remote"))
    return make_result(level_id,level_name,started,findings,output="\n".join(outputs),metadata={**session_metadata(config),"remote_enabled":True,"domain":domain})


def _latest_result(config: AppConfig, level: str):
    path=config.control_root_path/"latest"/level.lower()/"result.json"
    if not path.is_file(): return None
    try: return read_level_result(path)
    except Exception: return None


def correlation(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started=now(); findings=[]; session=active_session(config); session_id=str(session.get("session_id")) if session else ""
    observed=[]
    if not session_id:
        findings.append(Finding("kx.correlation.session",WARN,"No active diagnostic session found; correlation is limited.","correlation"))
    else:
        findings.append(Finding("kx.correlation.session",PASS,f"Correlating current diagnostic session {session_id}.","correlation"))
    failures=[]; warnings=[]; missing=[]
    expected = session.get("expected_levels", []) if session else []
    if not isinstance(expected, list) or not expected:
        expected = [f"N{number:02d}" for number in range(1, 11)]
    expected = [str(lid) for lid in expected if str(lid) not in {"N00", "N11"}]
    for lid in expected:
        result=_latest_result(config,lid)
        if result is None:
            missing.append(lid); continue
        if session_id and str(result.metadata.get("diagnostic_session_id","")) != session_id:
            missing.append(lid); continue
        observed.append((lid,result))
        if result.verdict in {FAIL,INFRA_ERROR,CONFIG_ERROR,"ERROR","BLOCKED"}: failures.append((lid,result))
        elif result.verdict == WARN: warnings.append((lid,result))
    if missing:
        findings.append(Finding("kx.correlation.coverage",WARN,"Some diagnostic domains were not executed in the current session.","correlation",evidence=", ".join(missing),recommendation="Run the full-local or connection-debug campaign for broader evidence."))
    else:
        findings.append(Finding("kx.correlation.coverage",PASS,"All diagnostic domains expected by this campaign have current-session evidence.","correlation",evidence=", ".join(expected)))

    ids={f.id for _,r in observed for f in r.findings if f.severity in {FAIL,INFRA_ERROR,CONFIG_ERROR,"ERROR"}}
    hypotheses=[]
    if any(x.startswith("kx.frontend.") for x in ids): hypotheses.append("frontend build/type/test failure")
    if any(x.startswith("kx.backend.") for x in ids): hypotheses.append("backend/Django/database failure")
    if any(x.startswith("kx.contract.") for x in ids): hypotheses.append("frontend↔backend API contract mismatch")
    if any(x.startswith("kx.runtime.") for x in ids): hypotheses.append("local runtime/browser smoke failure")
    if any(x.startswith("kx.jobs.") for x in ids): hypotheses.append("Celery/Redis/background-job failure")
    if any(x.startswith("kx.capsule.") for x in ids): hypotheses.append("capsule packaging/runtime-manager failure")
    if any(x.startswith("kx.remote.") for x in ids): hypotheses.append("deployed DNS/HTTP/Agent/runtime failure")
    if failures:
        evidence="; ".join(f"{lid}={r.verdict}" for lid,r in failures)
        findings.append(Finding("kx.correlation.failures",FAIL,"Blocking failures were detected in the current diagnostic session.","correlation",evidence=evidence,recommendation="Fix the earliest failing domain, then rerun the focused campaign."))
    elif warnings:
        findings.append(Finding("kx.correlation.failures",WARN,"No blocking failure was found, but warnings remain.","correlation",evidence="; ".join(f"{lid}={r.verdict}" for lid,r in warnings)))
    else:
        findings.append(Finding("kx.correlation.failures",PASS,"No blocking failure or warning was found in correlated current-session results.","correlation"))
    if hypotheses:
        findings.append(Finding("kx.correlation.hypotheses",WARN,"Likely failure domain(s): " + ", ".join(hypotheses),"correlation",evidence=" | ".join(hypotheses)))
    elif failures:
        findings.append(Finding("kx.correlation.hypotheses",WARN,"Failures exist but do not match a specialized correlation rule yet.","correlation"))
    else:
        findings.append(Finding("kx.correlation.hypotheses",PASS,"No failure-domain hypothesis required.","correlation"))
    return make_result(level_id,level_name,started,findings,metadata={"diagnostic_session_id":session_id,"campaign":session.get("campaign", "") if session else "","expected_levels":expected,"observed_levels":[lid for lid,_ in observed],"hypotheses":hypotheses})


CHECKS = {
    "N00": discovery,
    "N01": repository_static,
    "N02": backend,
    "N03": frontend,
    "N04": contracts,
    "N05": runtime_smoke,
    "N06": jobs,
    "N07": security,
    "N08": capsule_local,
    "N09": deployed,
    # N10 intentionally performs a broad deep/full-scan command when configured.
}


def deep_scan(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    started=now(); paths=target_paths(config); findings=[]; outputs=[]; frontend=paths["frontend"]; assert frontend is not None
    cmd=command_value(config,"frontend_full_scan")
    if cmd is None:
        script=frontend/"tools"/"full-scan.ps1"
        if script.is_file():
            shell="pwsh" if _find_tool("pwsh") else "powershell"
            cmd=[shell,"-NoProfile","-ExecutionPolicy","Bypass","-File",str(script)]
    finding,step=command_probe(config,finding_id="kx.deep.frontend-full-scan",label="Konnaxion full frontend diagnostic scan",command=cmd,cwd=frontend,timeout=2400,optional=True,recommendation="Keep frontend/tools/full-scan.ps1 or configure konnaxion.commands.frontend_full_scan.")
    findings.append(finding)
    if step: outputs.append(step.output_tail)
    backend_dir=paths["backend"]; assert backend_dir is not None
    cmd=command_value(config,"backend_full_tests") or ["python","-m","pytest","-q"]
    finding,step=command_probe(config,finding_id="kx.deep.backend-tests",label="Full backend pytest suite",command=cmd,cwd=backend_dir,timeout=2400,optional=True)
    findings.append(finding)
    if step: outputs.append(step.output_tail)
    return make_result(level_id,level_name,started,findings,output="\n\n".join(outputs),metadata={**session_metadata(config),"cwd":str(paths["root"])})

CHECKS["N10"] = deep_scan
CHECKS["N11"] = correlation


def run_domain(config: AppConfig, level_id: str, level_name: str) -> LevelResult:
    fn=CHECKS[level_id]
    return fn(config,level_id,level_name)
