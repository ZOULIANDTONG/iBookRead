# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iBookRead is a command-line document reader supporting multiple formats (EPUB, MOBI, TXT, Markdown). It features two modes: a default plain-text output mode and an optional interactive UI mode with Rich-based terminal interface.

## Common Commands

### Development Setup
```bash
# Clone and setup
git clone https://github.com/yourusername/iBookRead.git
cd iBookRead

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=ibook_reader --cov-report=term

# Run specific test file
pytest tests/unit/test_parsers.py

# Run single test
pytest tests/unit/test_parsers.py::TestEpubParser::test_parse_basic
```

### Building and Distribution
```bash
# Install build tools
pip install build

# Build distribution packages
python -m build

# Install from wheel
pip install dist/ibook_reader-1.0.0-py3-none-any.whl
```

### Running the Application
```bash
# Plain text mode (default)
ibook book.epub

# Interactive UI mode
ibook --ui book.epub

# Jump to specific position (UI mode only)
ibook --ui --page 10 book.epub
ibook --ui --chapter 5 book.epub
ibook --ui --percent 50 book.epub
```

## Architecture Overview

### Core Components

**Document Flow**: File → Parser → Document → Paginator → Page → UI Renderer

1. **Parsers** (`ibook_reader/parsers/`): Convert various file formats into a unified Document model
   - `factory.py`: ParserFactory selects appropriate parser based on file format
   - `base.py`: BaseParser abstract class defining parser interface
   - Format-specific parsers: `epub_parser.py`, `mobi_parser.py`, `txt_parser.py`, `markdown_parser.py`
   - All parsers return a Document object with structured chapters

2. **Models** (`ibook_reader/models/`): Core data structures
   - `document.py`: Document and Chapter dataclasses representing parsed content
   - `bookmark.py`: Bookmark model for saving reading positions
   - `progress.py`: ReadingProgress model for tracking current position

3. **Core Engine** (`ibook_reader/core/`):
   - `paginator.py`: The Paginator class splits document content into terminal-sized pages
     - Handles text wrapping with `get_display_width()` for CJK character support
     - Implements smart pagination considering terminal dimensions
     - Small documents (<1000 lines) are fully cached; large documents use windowed caching
   - `format_detector.py`: Detects file format from extension and content

4. **Services** (`ibook_reader/services/`): Business logic layer
   - `reader_service.py`: ReaderService is the main controller coordinating all operations
   - `auth_service.py`: Handles password authentication (UI mode only)
   - `bookmark_service.py`: Manages bookmark CRUD operations
   - `progress_service.py`: Handles reading progress persistence

5. **UI Layer** (`ibook_reader/ui/`): Rich-based terminal interface (UI mode only)
   - `renderer.py`: Creates and updates Rich Layout with header/content/footer
   - `input_handler.py`: Captures and processes keyboard input (Vim-style keys)
   - `components.py`: Reusable UI components (help panel, message box)

6. **CLI** (`ibook_reader/cli.py`): Application entry point
   - `main()`: Parses arguments and routes to plain text or UI mode
   - `plain_text_mode()`: Outputs full document content directly or via pager
   - `start_reader()`: Initializes UI mode with authentication and services
   - `reading_loop()`: Main event loop handling keyboard input in UI mode

### Key Design Patterns

**Parser Factory Pattern**: `ParserFactory.create_parser()` uses FormatDetector to instantiate the correct parser without tight coupling.

**Service Layer**: Business logic is separated into service classes (ReaderService, BookmarkService, ProgressService, AuthService) which can be dependency-injected or instantiated with defaults.

**Page Model**: The `Page` class (in `paginator.py`) represents a single screen of content with metadata (page_number, chapter_index). The Paginator generates pages on-demand and caches based on document size.

**Two-Mode Architecture**:
- Plain text mode: Direct output pipeline bypassing UI/authentication for piping/scripting
- UI mode: Full interactive experience with authentication, progress tracking, and Rich interface

### Data Storage

All persistent data stored in `~/.ibook_reader/`:
- `config.json`: User configuration including password hash with salt
- `progress.json`: Reading progress keyed by file hash
- `bookmarks/`: Individual JSON files per document (named by file hash)

## Important Implementation Details

### Text Display Width Calculation
The `utils/text_utils.py::get_display_width()` function handles CJK (Chinese/Japanese/Korean) characters which occupy 2 terminal columns. The Paginator uses this for accurate line wrapping.

### File Hash for Progress/Bookmarks
Progress and bookmarks are keyed by file hash (MD5 of first 1MB + file size), not file path, so moving files preserves reading state.

### Terminal Size Handling
The Paginator dynamically adjusts to terminal size changes via `update_terminal_size()`, which recalculates page breaks and attempts to maintain the current chapter position.

### Authentication Flow (UI Mode)
On first launch with `--ui`, AuthService prompts for optional password setup. Password is stored as SHA-256 hash with random salt in `config.json`. Plain text mode skips authentication entirely.

## Testing Notes

- 178 test cases with 71% coverage
- Unit tests in `tests/unit/` organized by module
- Integration tests in `tests/integration/`
- Test fixtures for sample documents in `tests/fixtures/` (if present)
- Mock terminal sizes in paginator tests to ensure consistent results

## Code Style

- Python 3.8+ with type hints
- PEP 8 compliant
- Dataclasses for models
- Docstrings follow Google style
- Rich library for all UI rendering (avoid print in UI code)
