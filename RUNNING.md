# Running tgfs-webdav — step by step

Telegram-backed WebDAV server (Python fork of TheodoreKrypton/tgfs). Serves your
Telegram file channels as a WebDAV share on port **1900**.

There are two ways to run it:

- **A. Docker** (recommended — matches the deploy setup)
- **B. Native / Poetry** (for local development)

> ⚠️ **Network requirement:** the host must allow outbound Telegram (MTProto).
> The dev sandbox blocks MTProto, so the live login (step 6/B-step 5) only works
> on a real host (your existing tgfs box is known-good).

---

## 0. One-time: prepare secrets (both paths)

Secrets never live in `config.yaml`. It only holds structure and `${VAR}`
placeholders, resolved at startup from a gitignored `.env`. A missing variable
fails fast with a clear error.

```bash
cd ~/github/tgfs          # or wherever you cloned it
cp .env.example .env
```

Edit `.env` and fill in every value (all are required):

| Variable            | What it is                                              |
|---------------------|---------------------------------------------------------|
| `TG_API_HASH`       | Telegram API hash (api_id `37723388` is already in yaml) |
| `TG_BOT_TOKEN_1`    | First bot token from @BotFather                         |
| `TG_BOT_TOKEN_2`    | Second bot token                                        |
| `TGFS_USER_PASSWORD`| WebDAV password for user `guny`                         |
| `TGFS_JWT_SECRET`   | Any long random string (e.g. `openssl rand -hex 32`)    |
| `GH_PAT_MOVIES`     | GitHub fine-grained PAT, Contents R/W on `gunysa1/tgfs-movies` |
| `GH_PAT_TV`         | GitHub fine-grained PAT, Contents R/W on `gunysa1/tgfs-tv`     |

> 🔐 If these were ever shared in plaintext, **rotate them now**: BotFather
> `/revoke` for bot tokens, GitHub → regenerate for the PATs — then paste the
> new values into `.env`. `.env` and `config.yaml` are gitignored; never commit them.

Confirm they’re ignored:

```bash
git check-ignore .env config.yaml   # should print both
```

---

## A. Run with Docker (recommended)

### A1. Build and start

```bash
docker compose up -d --build
```

Compose mounts `config.yaml` read-only at `/config/config.yaml` and `.env` into
the container’s data dir, then starts the server on host port 1900.

### A2. Watch the logs until it’s ready

```bash
docker compose logs -f
```

Wait for: bots log in → both channels (Movies + TV) initialize → metadata GitHub
repos resolve → server listening on **0.0.0.0:1900**. `Ctrl-C` stops following
(the container keeps running).

### A3. Verify end-to-end (WebDAV)

```bash
PW='<the TGFS_USER_PASSWORD you set>'

# List root
curl -u guny:"$PW" -X PROPFIND http://localhost:1900/webdav -H 'Depth: 1'

# Upload a test file
echo hello > /tmp/hello.txt
curl -u guny:"$PW" -T /tmp/hello.txt http://localhost:1900/webdav/hello.txt

# Download it back (should print "hello")
curl -u guny:"$PW" http://localhost:1900/webdav/hello.txt
```

### A4. Manage

```bash
docker compose ps        # status
docker compose logs -f   # follow logs
docker compose restart   # restart after editing .env
docker compose down      # stop (named volume tgfs-data keeps the TG sessions)
```

Editing `.env` or `config.yaml` requires a `docker compose restart` (or
`up -d` to also pick up a rebuild) to take effect.

---

## B. Run natively (Poetry, for development)

### B1. Install Poetry (once)

```bash
curl -sSL https://install.python-poetry.org | python3 -
# ensure ~/.local/bin is on PATH
```

### B2. Install dependencies (in-project .venv)

```bash
cd ~/github/tgfs
poetry install
```

### B3. Sanity-check the toolchain (optional but recommended)

```bash
poetry run make test    # runs the suite against config-test.yaml
poetry run make ruff
poetry run make mypy
```

### B4. Point the app at this directory’s config + .env

The app reads `config.yaml` and `.env` from `TGFS_DATA_DIR` (default `~/.tgfs`).
For a local run, point it at the repo dir:

```bash
export TGFS_DATA_DIR=.
export TGFS_CONFIG_FILE=config.yaml
```

### B5. Start the server

```bash
poetry run python main.py
```

Watch stdout for the same readiness signs as A2, then verify with the same
`curl` commands as **A3**.

Stop with `Ctrl-C`.

---

## Mounting the share (either path)

Point any WebDAV client at `http://<host>:1900/webdav` with user `guny` and your
password. With rclone:

```bash
rclone config   # new remote, type = webdav, vendor = other,
                # url = http://<host>:1900/webdav, user = guny
rclone mount tgfs:/ /mnt/tgfs --vfs-cache-mode full
```

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Config references undefined environment variable: ${X}` | A var is missing from `.env`. Fill it in. |
| Hangs / `Connection reset` during bot login | Host can’t reach Telegram (MTProto blocked). Run on a network that allows it. |
| `401 Unauthorized` on curl | Wrong `guny` password — must match `TGFS_USER_PASSWORD` in `.env`. |
| GitHub metadata errors | PAT lacks Contents R/W, or wrong repo/branch (`master`). |
| Changed `.env` but no effect | Docker: `docker compose restart`. Native: restart `python main.py`. |

See `DEPLOY.md` for the production/host deployment notes.
