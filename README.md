# fedora-bus-listener

Listens to the Fedora message bus for stable kernel updates and launches EC2 instances to build kmod RPMs for each supported architecture.

## How it works

1. Subscribes to `org.fedoraproject.prod.bodhi.update.complete.stable` on the Fedora AMQP bus
2. Filters for kernel package updates
3. For each detected update, launches one EC2 instance per architecture (`x86_64`, `aarch64`) with a userdata script that builds and publishes the kmod RPM

## Configuration

All configuration is via environment variables:

| Variable | Description |
|---|---|
| `AMI_X86_64` | AMI ID for x86_64 builder instances |
| `AMI_AARCH64` | AMI ID for aarch64 builder instances |
| `REPO_BUCKET_NAME` | S3 bucket where built RPMs are published |
| `GPG_SECRET_NAME` | AWS Secrets Manager secret name for the GPG signing key |

A `fedora-messaging` config file is also required, pointed to by `FEDORA_MESSAGING_CONF`.

## Running

The service is managed by systemd:

```bash
systemctl enable --now fedora-message-dispatcher@ec2-user.service
```

## Building

Requires `rpkg` and `pyproject-rpm-macros`:

```bash
rpkg builddep
rpkg local --outdir build/
```

## Releasing

Tag the commit using the rpkg tag format and push:

```bash
git tag -a fedora-bus-listener-1.0-1 -m "fedora-bus-listener-1.0-1"
git push origin fedora-bus-listener-1.0-1
```

This triggers the GitHub Actions release workflow which builds the RPM and attaches it to a GitHub release.
