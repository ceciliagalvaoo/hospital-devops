# Hospital Management — DevOps Project

A simple hospital administration web application for managing
patients, doctors, appointments and medical records.
The project focuses on building an automated DevOps pipeline.

**GitHub Project (backlog and Kanban board):** <https://github.com/users/ceciliagalvaoo/projects/3>.
The way the backlog is tracked on GitHub is described in [docs/github-project.md](docs/github-project.md).

## Quickstart

Run the application with its PostgreSQL database (requires Docker with Docker Compose):

```powershell
Copy-Item .env.example .env       # Linux/macOS: cp .env.example .env
docker compose up --build -d
docker compose run --rm app python -m app.seed
```

Then open <http://127.0.0.1:8000/login> and log in as `dev.receptionist`, `dev.doctor` or `dev.administrator` with the `SEED_PASSWORD` from `.env`. Stop the stack with `docker compose down`.

Run the tests (requires Python 3.12 or later):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
docker compose --profile test up -d --wait test-db
pytest --cov=app
```

Details: [running locally](docs/development/running-locally.md), [testing and code quality](docs/development/testing.md).

## Documentation

The full documentation is in [docs/](docs/README.md):

| Topic | Documents |
| --- | --- |
| Product | [requirements and roles](docs/requirements.md), [product backlog](docs/backlog.md), [task decomposition](docs/tasks.md), [estimation](docs/estimation.md) |
| Process | [sprint planning](docs/planning.md), [GitHub Project](docs/github-project.md), [sprint records](docs/sprints/) |
| Architecture | [architecture](docs/architecture.md), [tools and technology stack](docs/tooling.md) |
| Development | [running locally](docs/development/running-locally.md), [testing](docs/development/testing.md), [continuous integration](docs/development/ci.md), [migrations](docs/development/migrations.md), [accounts and access control](docs/development/authentication.md), [branching strategy](docs/development/branching-strategy.md), [Git workflow](docs/development/git-workflow.md) |
| Delivery | [container image](docs/docker-build.md), [versioning](docs/versioning.md), [publishing](docs/publishing.md) |
