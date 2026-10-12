---
name: vapor-vps-deploy
description: Provision or migrate a production Ubuntu VPS for a Swift/Vapor backend, optionally with Node/Next.js services, PostgreSQL, systemd, Nginx, TLS, and CI deployment. Use for new-server setup, provider or region migration, production cutover, rollback planning, and post-deploy operations; do not use for ordinary application-code deployment to an already configured host.
---

# Vapor VPS Deploy

Build or migrate a production host without losing data, exposing secrets, or running two schedulers at once.

## Establish scope before mutation

Identify the target application and treat any other repository or server mentioned by the user as a reference unless explicitly designated as the target. Resolve the application/repository, cloud project and region, server name/configuration, domains, services/ports, runtime user/paths, database and persistent files, scheduled jobs, deployment mechanism, and rollback window.

Before creating a billable resource, show the resolved application name and server configuration. Check for an existing server with that name. Authorization to create one application’s server does not authorize creating a similarly configured server for another application.

## Choose the workflow

- For a new empty host, read [references/ubuntu-vps-runbook.md](references/ubuntu-vps-runbook.md) through “Application staging,” then apply only the components the project uses.
- For a migration or region move, read the entire runbook. Separate reversible preparation from cutover and preserve the old host until rollback is no longer needed.
- For an outage, determine whether the source VM is powered off, unreachable, or unavailable only for new orders. Do not assume that a sold-out region means an existing VM or its data is lost.

## Invariants

- Never print, persist in Git, or copy production passwords, API keys, private keys, database URLs, or environment-file contents into logs. Filter cloud API responses to required fields because server-list responses may contain generated passwords.
- Prefer SSH keys and verify a non-root login before relying on it.
- Keep PostgreSQL and application ports bound to loopback. Expose only Nginx on 80/443.
- Run production processes as native systemd services and keep unit files in the repository when practical.
- Give CI only narrowly scoped passwordless `systemctl restart` and `systemctl is-active` permissions. Never grant `NOPASSWD: ALL`.
- Keep scheduled jobs disabled on a staging host. At cutover, ensure exactly one production scheduler is active.
- Preserve encryption keys required to decrypt existing stored data.
- Validate backups before replacing a database. Compare schema/table counts and meaningful row counts after restore.
- Test Nginx before reload and test the new host directly before DNS changes.
- Do not delete the source server, database, certificates, backups, or bridge until DNS caches have expired and production has completed a suitable observation period.

## Execution and verification

Derive placeholders from the actual project instead of copying example IPs, domains, users, ports, or service names. Inspect repository-owned systemd, Nginx, sudoers, and CI files before installing them. Adapt runtime versions to project lockfiles and manifests rather than reproducing historical versions.

Pause immediately before destructive database replacement or DNS cutover if not already explicitly authorized. Report the source of truth, rollback path, and expected write interruption.

Verify systemd state/restarts, loopback and public listeners, local health, public HTTPS/certificates, database ownership/migrations, scheduler exclusivity, region-sensitive external providers, CI deployment, and authoritative/public DNS. Record durable, non-secret production facts in project operations documentation.
