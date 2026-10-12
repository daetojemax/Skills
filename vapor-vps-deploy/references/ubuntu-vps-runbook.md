# Ubuntu VPS production runbook

Replace every placeholder from inspected project state and omit components the application does not use.

## 1. Inventory and recovery

Capture the current host, directories, service manager, ports, database version/name/owner, persistent files, domains, certificates, background jobs, deployment keys, CI secrets, and external integrations.

Before relying on a source host, verify provider power state, incidents, snapshots/backups, SSH, and public health separately. Do not promote a blank replacement while the only current database is unreachable.

Provision plain Ubuntu 24.04 LTS without marketplace software. A proven small Swift/Next.js build host shape is 3 vCPU, 3–4 GB RAM, 50 GB SSD, 50 Mbps, plus 4 GB swap. Adjust from measured workload and build memory.

## 2. Base host

Set an application-specific hostname and create a non-root runtime/deploy user. Copy only intended public SSH keys, use `700`/`600` modes, and verify a separate SSH login before closing root access.

For a low-memory build host, create persistent swap:

```bash
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
swapon --show
```

Typical Vapor/Next.js packages:

```bash
apt-get update
apt-get install -y ca-certificates curl git rsync unzip pkg-config \
  build-essential clang libssl-dev libcurl4-openssl-dev \
  libxml2-dev zlib1g-dev nginx certbot python3-certbot-nginx \
  postgresql postgresql-contrib
```

## 3. Runtimes and database

Install Swift through official Swiftly as the runtime user. Select the version required by `swift-tools-version`, `Package.resolved`, and CI. Constrain release-build parallelism to available memory.

If Node services exist, install the repository-supported version and use a stable absolute Node path in systemd. Strict Next.js units may require `AF_NETLINK` in `RestrictAddressFamilies` because Node reads network interfaces during startup.

Enable PostgreSQL and confirm it listens only on `127.0.0.1:5432`. Create a dedicated role and owned database with a generated password that never enters Git or command history. Verify version, owner, authentication, and extensions.

Keep configuration and secrets outside the checkout under `/etc/<app>/`, normally root-owned with the runtime-user group and mode `640`. During parallel staging disable scheduled jobs. Preserve any encryption key required for existing ciphertext.

## 4. Application staging

Create an application directory owned by the runtime user. Prefer CI or `rsync` with explicit exclusions for build caches, `.env` files, and persistent uploads. Never use broad `--delete` without protecting server-owned data.

Build components sequentially on small hosts: Vapor release/tests, frontend install/build, then admin install/tests/build. For standalone Next.js output, copy `public` and `.next/static` into the standalone tree when required.

## 5. Services, Nginx, and TLS

Keep systemd units in the repository and install them into `/etc/systemd/system/`. Run as the runtime user, load environment files from `/etc/<app>/`, bind apps to loopback, and configure restart policy and compatible hardening.

Install a narrow sudoers file for CI allowing only exact application services/actions; validate with `visudo -cf`.

Map public domains to loopback ports in Nginx, preserving upload limits and long-request timeouts. Always run `nginx -t` before reload. Use Certbot for new certificates or transfer an existing Let’s Encrypt tree directly between trusted hosts. Never store certificates locally or in Git.

Before DNS cutover test every TLS host against the new IP:

```bash
curl --resolve <domain>:443:<new-ip> -I https://<domain>/<health-path>
```

## 6. Migration and cutover

Rehearse a database dump/restore while old production remains writable. Use PostgreSQL custom format with `--no-owner --no-privileges`; validate with `pg_restore --list`. Restore under the new application role and compare schema and row counts.

Transfer uploads, certificates, and environment files directly between trusted hosts, never through agent output or Git.

Final order:

1. Confirm builds, services, Nginx/TLS, CI, and provider calls.
2. Begin a controlled write stop and stop the old backend.
3. Take and validate the final database dump.
4. Synchronize persistent uploads after writes stop.
5. Stop the staged new backend.
6. Replace the rehearsed database only after validating the final dump.
7. Restore with `--exit-on-error`, the intended role, and no source ownership/privileges.
8. Compare source/destination tables and row counts.
9. Enable jobs only on the new backend and start it.
10. Verify local and direct-to-new-host HTTPS health.
11. Optionally bridge stale-DNS clients through old Nginx.
12. Update and prove CI workflows, then change DNS.

Never run two schedulers or restart the old backend after the new database becomes authoritative.

## 7. Verification and rollback

Confirm app ports are loopback-only and only Nginx exposes 80/443. Inspect service state/restarts, health, HTTPS, certificate renewal, PostgreSQL, logs, disk, memory/swap, and scheduled jobs.

Test region-sensitive APIs from the new host without printing credentials. Report only provider/model, HTTP status, and a redacted result.

Check authoritative DNS before public resolvers and leave any bridge for at least the prior TTL. Before new writes, rollback by stopping new services, restoring DNS/proxy configuration, and starting old services. After new writes, never simply start the old database; migrate changes back or keep the new database authoritative.

Retain the source host/database, final validated dump, pre-cutover Nginx config, bridge config, certificates, and written rollback sequence until the observation window ends.
