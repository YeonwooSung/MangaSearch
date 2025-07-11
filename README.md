# MangaSearch

## Running Instructions

1. Set up a ParadeDB based database (using docker in this example).
    ```bash
    # Build custom image
    docker build -t mangasearch-paradedb -f docker/Dockerfile.db .

    # Run the container
    docker run --name mangasearch-paradedb -e POSTGRES_PASSWORD=password -p 5432:5432 -d mangasearch-paradedb
    ```

2. Use uv to install dependencies:
    ```bash
    uv venv

    uv pip install -r requirements.txt
    ```

3. Run the application (with uv):
    ```bash
    uv run python3 -m manga_search.main
    ```

## References

[Mangabaka](https://mangabaka.dev/) is a web service for manga search, which uses paradedb as a backend DB.
