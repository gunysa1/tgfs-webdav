# Deploying tgfs-webdav (Docker)

This is the Python WebDAV variant of tgfs (fork of TheodoreKrypton/tgfs).
These steps run it on a host that has working Telegram connectivity.

> The dev sandbox this was prepared in filters Telegram's MTProto protocol, so
> Phases 3–5 (live login + WebDAV round-trip) must be completed on a real host.
> Steps 1–2 (fork, dependency refresh, tests/lint/types, image build) are
> already verified.

## Prerequisites

- Docker + Docker Compose on the host
- A network that allows outbound Telegram (MTProto) — same as your existing
  tgfs deployment
- Your `config.yaml` (it is **gitignored**, so it is NOT in the repo — you must
  place it on the host yourself)

## 1. Get the code

```bash
git clone git@github.com:gunysa1/tgfs-webdav.git
cd tgfs-webdav
git checkout fork-update-deploy   # until merged to master
```

## 2. Provide config.yaml and secrets.env

Secrets live in a **`secrets.env`** file, not in `config.yaml`. `config.yaml` only
holds non-secret structure and references secrets via `${VAR}` placeholders, which
are resolved at startup from the environment (or `$TGFS_DATA_DIR/.env`). A missing
variable fails fast with a clear error.

The file is named `secrets.env` (not `.env`) so Docker Compose does not auto-load
it for its own `${...}` interpolation — that would warn on and blank any `$` in a
secret value.

- Place your `config.yaml` in the repo root (next to `docker-compose.yml`).
- Create `secrets.env` from the template and fill in real values:
  ```bash
  cp secrets.env.example secrets.env
  # edit secrets.env — set TG_API_HASH, TG_BOT_TOKEN_1/2, TGFS_USER_PASSWORD,
  # TGFS_JWT_SECRET, GH_PAT_MOVIES, GH_PAT_TV
  ```

Both `config.yaml` and `secrets.env` are gitignored — never commit them. To rotate
a secret later, edit only the relevant line in `secrets.env`; `config.yaml` never
changes.

Compose bind-mounts `secrets.env` read-only to `$TGFS_DATA_DIR/.env` in the
container, so the app loads it directly (Compose does not interpolate the values).

## 3. Build and run

```bash
docker compose up -d --build
docker compose logs -f
```

Watch the logs until the bots log in, both channels (Movies + TV) initialize,
and the metadata GitHub repos resolve. The server then listens on port **1900**.

## 4. Verify end-to-end (WebDAV)

```bash
# List root (use a user from config.yaml, e.g. guny)
curl -u guny:'<password>' -X PROPFIND http://localhost:1900/webdav -H 'Depth: 1'

# Upload a test file
echo hello > /tmp/hello.txt
curl -u guny:'<password>' -T /tmp/hello.txt http://localhost:1900/webdav/hello.txt

# Download it back
curl -u guny:'<password>' http://localhost:1900/webdav/hello.txt
```

Or mount with rclone (WebDAV backend, vendor = other, URL `http://<host>:1900/webdav`).

## Notes

- **Data volume:** Telegram session files persist in the named volume
  `tgfs-data` (mounted at `/home/tgfs/.tgfs`, owned by uid 1000). First start
  generates the sessions.
- **Config path:** mounted read-only at `/config/config.yaml`; the container
  reads it via `TGFS_CONFIG_FILE`.
- **Security:** the bot tokens and GitHub PATs in `config.yaml` were shared in
  plaintext during setup — consider rotating them.
- **Upstream updates:** `git fetch upstream && git merge upstream/master`
  (remote `upstream` = TheodoreKrypton/tgfs).
