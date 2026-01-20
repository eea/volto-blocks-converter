# Project Context: Volto Blocks Converter

## Overview
This project is a Python-based microservice designed to convert content between **Volto blocks** (JSON structure used by Plone/Volto) and **HTML**. Its primary use case is facilitating content translation (e.g., via eTranslation) by converting structured blocks into a flat HTML format that translation engines can process, and then converting the translated HTML back into Volto blocks.

The application is built using the **Litestar** (formerly Starlite) web framework and **lxml** for HTML processing.

## Key Features
- **Blocks to HTML (`blocks2html`):** Serializes complex Volto block structures (Slate, Tables, Teasers, etc.) into an HTML representation, preserving metadata in attributes.
- **HTML to Blocks (`html2blocks`):** Reconstructs Volto blocks from the specific HTML structure.
- **Slate Conversions:** Specialized handling for SlateJS rich text data (`slate2html`, `html2slate`).

## Tech Stack
- **Language:** Python 3.10+
- **Web Framework:** Litestar (Starlite)
- **Server:** Uvicorn
- **XML/HTML Processing:** lxml, BeautifulSoup4
- **Testing:** Pytest

## Project Structure
- `app/`: Source code directory.
    - `main.py`: Entry point, API route definitions (`/html`, `/toblocks`, `/blocks2html`, etc.).
    - `blocks2html.py`: Core logic for serializing blocks to HTML.
    - `html2blocks.py`: Logic for deserializing HTML back to blocks.
    - `slate2html.py` / `html2slate.py`: Helpers for SlateJS rich text.
- `tests/`: Test suite.
- `docker-entrypoint.sh`: Startup script.
- `Makefile`: Command aliases.

## Development Commands

### Building and Running
The project is designed to run in a Docker environment, but can be run locally if dependencies are installed.

*   **Start Server:**
    ```bash
    make start
    # OR directly:
    # ./docker-entrypoint.sh
    ```
    This runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

### Testing
*   **Run Tests:**
    ```bash
    make test
    # OR directly:
    # pytest
    ```

## Conventions
*   **Code Location:** All application logic resides in the `app/` package.
*   **Dependency Management:** `pyproject.toml` suggests Poetry, though a `requirements.txt` is also available.
*   **Type Hinting:** Code uses Python type hints (`typing` module).
