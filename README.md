# PokeVault

Private, offline-ready Pokémon card collection and valuation stack. Runs entirely on a single server with Docker Compose and stores all catalog data + images locally.

## Architecture
- **reverse-proxy:** Nginx (serves `/media`, proxies `/api` and frontend)
- **db:** PostgreSQL
- **cache/queue:** Redis
- **backend:** FastAPI API server
- **worker:** background RQ worker
- **frontend:** React + Tailwind (Vite dev server)

## Setup

1. Copy environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Backend API will be proxied at `http://localhost:8080/api` and the frontend at `http://localhost:8080/`.

## Admin bootstrap commands (CLI)

Run inside the backend container:

```bash
docker compose exec backend python -m app.scripts.init_db
```

```bash
docker compose exec backend python -m app.scripts.import_catalog
```

```bash
docker compose exec backend python -m app.scripts.prefetch_images
```

```bash
docker compose exec backend python -m app.scripts.seed_prices
```

### Available modes

- `PREFETCH_MODE=owned|set|all` (default: owned)
- `SEED_MODE=tracked|all` (default: tracked)

Example:

```bash
PREFETCH_MODE=all docker compose exec backend python -m app.scripts.prefetch_images
```

## Storage layout

Media volume is mounted at `/media` in the containers and stored by Docker in the `media` volume. The official image downloader will write to:

```
/media/official/<set_code>/<card_number>/<small|large>.jpg
```

User uploads are stored at:

```
/media/uploads/<user_id>/
```

## Expected disk usage

- Full English catalog images (small + large) will require **tens to hundreds of GB** depending on dataset. Plan for a dedicated disk and expand the Docker volume if needed.
- PostgreSQL data grows with price history and portfolio snapshots; allocate a few GB for the database volume.

## Development vs Production

- **Development:** `docker compose up` uses Vite dev server on port 5173 and proxied via Nginx at 8080.
- **Production:** build the frontend separately (`npm run build`) and serve static assets through Nginx or the backend.

## Admin UI Setup Wizard

On first admin login, use the Admin page to run:

1. **Import Catalog**
2. **Download Images** (all or selective)
3. **Seed Prices** (optional)
4. **Invite Friends**

Progress is tracked in the job runs list.
