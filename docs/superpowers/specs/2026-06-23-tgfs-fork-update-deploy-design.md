# tgfs Fork — Update, Run & Deploy (Design)

**Date:** 2026-06-23
**Owner:** gunysa1 (guny)
**Status:** Approved

## Goal

Stand up a working, self-owned fork of the Python tgfs project
(TheodoreKrypton/tgfs — "Telegram becomes a WebDAV server"): dependencies
refreshed, runs locally, connected to the real Telegram channels, and deployed
via Docker.

## Decisions

- **Update strategy:** Conservative — refresh `poetry.lock` to latest *within*
  existing version constraints; only bump majors where something is actually
  broken.
- **Deploy target:** Docker (repo ships a `Dockerfile`; Docker already installed).
- **Fork style:** Public GitHub fork via `gh repo fork` (gunysa1/tgfs), linked to
  upstream so upstream updates can be pulled.

## Environment (verified 2026-06-23)

- Python 3.13.5 ✓ (meets `>=3.13`)
- Docker installed ✓ · Poetry NOT installed (install in Phase 2)
- `gh` authed as gunysa1 ✓
- Original git remote: `TheodoreKrypton/tgfs`
- `config.yaml` is gitignored ✓ and holds real secrets (2 bot tokens, 2 channels,
  2 GitHub PATs, JWT secret, `guny` password)
- `.tgfs/` dir is root-owned (leftover from a prior Docker run) — must fix
- Metadata repos `gunysa1/tgfs-movies` & `gunysa1/tgfs-tv` are **private** (exist)

## Config summary

- Telegram lib: telethon; 2 bots; 2 private channels
- Channel `1003982678825` → **Movies**, metadata in `gunysa1/tgfs-movies`
- Channel `1003752888269` → **TV**, metadata in `gunysa1/tgfs-tv`
- WebDAV user `guny`; server `0.0.0.0:1900`; download chunk 1024 KB; JWT HS256 7d

## Phases (each gated by verification before moving on)

1. **Fork hygiene** — `gh repo fork` → origin=fork, upstream=original; fix
   root-owned `.tgfs/`.
2. **Conservative dependency update** — install Poetry; `poetry lock`+`install`;
   `make ruff/mypy/test`; fix only breakage. **Gate: tests green.**
3. **Run locally** — `poetry run python main.py`; **Gate:** server on :1900, bots
   login, both channels init, metadata repos resolve.
4. **End-to-end check** — WebDAV list/upload/download a small file with `guny`
   creds. **Gate:** round-trip succeeds.
5. **Deploy via Docker** — build from `Dockerfile`; run with `config.yaml` +
   persistent data volume + port 1900. **Gate:** stays up, reachable, survives
   restart.

## Out of scope

New features, rebrand/rename, aggressive major-version bumps, GitHub Actions/
frontend pieces.

## Risks

- Metadata repos missing/inaccessible to the PAT → metadata layer fails.
- Lockfile refresh (Telethon/FastAPI/Pyrogram) introducing breakage.
- Docker volume + `.tgfs` permission interaction.
- Secrets already shared in plaintext — consider rotating bot tokens & PATs.
