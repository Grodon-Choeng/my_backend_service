# My Backend Service

A modern, high-performance backend service built with FastAPI, Tortoise-ORM, and other great technologies.

## About The Project

This project serves as a template for building robust and scalable backend services with Python. It includes a complete setup for asynchronous database operations, Redis caching, dependency management with `uv`, and a complete testing and linting setup.

### Built With

* [FastAPI](https://fastapi.tiangolo.com/)
* [Tortoise-ORM](https://tortoise.github.io/)
* [Pydantic](https://pydantic-docs.helpmanual.io/)
* [Redis](https://redis.io/)
* [MySQL](https://www.mysql.com/)
* [Docker](https://www.docker.com/)
* [uv](https://github.com/astral-sh/uv)

## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

* Python 3.12+
* Docker and Docker Compose
* `uv` package manager

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/your_username_/my-backend-service.git
   ```
2. Install Python packages
   ```sh
   uv pip install -e .[dev]
   ```
3. Start the services
   ```sh
   docker-compose up -d
   ```

## Usage

To run the application, use the following command:

```sh
uvicorn src.main:app --reload
```

The application will be available at `http://localhost:8000`.

## Running Tests

To run the tests, use the following command:

```sh
pytest
```

To run the tests with coverage, use the following command:

```sh
pytest --cov=src
```

## Database Migrations

This project uses `aerich` to manage database migrations.

### Initialize migrations

To initialize the migrations, run the following command:

```sh
aerich init-db
```

### Create a new migration

To create a new migration, run the following command:

```sh
aerich migrate
```

### Apply migrations

To apply the migrations, run the following command:

```sh
aerich upgrade
```

## Deployment

This project is set up to be deployed with Docker. A `Dockerfile` is provided to build a production-ready image.

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Distributed under the MIT License. See `LICENSE` for more information.