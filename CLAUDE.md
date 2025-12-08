# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests using Docker (recommended)
cd .docker && docker-compose -f docker-compose.gh.yml run qgis-testing-environment

# Run tests manually with pytest (requires QGIS environment)
xvfb-run pytest -v

# Run specific test file
xvfb-run pytest koordinates/test/test_api_utils.py -v
```

### Installation
```bash
# Install plugin symlink to QGIS for development
python helper.py install

# Install to specific QGIS profile
python helper.py install myprofile

# Package plugin for distribution
python helper.py package

# Package with version
python helper.py package v1.2.3
```

### Linting
```bash
# Run flake8
flake8 koordinates/

# Run black formatter
black koordinates/

# Install pre-commit hooks
pre-commit install --install-hooks
```

## Architecture

### Plugin Structure

This is a QGIS plugin that provides integration with Koordinates data hosting. The main entry point is `koordinates/plugin.py` which defines `KoordinatesPlugin`.

**Core Components:**
- `koordinates/plugin.py`: Main plugin class (`KoordinatesPlugin`) instantiated by QGIS via `classFactory()`
- `koordinates/api/`: API client and data models for Koordinates service
  - `client.py`: Singleton `KoordinatesClient` handles HTTP requests to Koordinates API
  - `data_browser.py`: `DataBrowserQuery` for filtering and searching datasets
  - `dataset.py`, `repo.py`: Data model classes
- `koordinates/gui/`: All UI components and Qt widgets
  - `koordinates.py`: Main dock widget (`Koordinates`) - the primary UI panel
  - `dataset_browser_items.py`: Tree view items for displaying datasets
  - `dataset_dialog.py`: Dataset detail view
  - `login_widget.py`: OAuth login interface
- `koordinates/core/`: Core business logic
  - `kart_operation_manager.py`: Manages Kart repository clone operations (as Qt model)
  - `kart_task.py`: Background tasks for Kart operations (`KartCloneTask`)
  - `kart_utils.py`: Integration with Kart plugin (optional dependency)
- `koordinates/auth.py`: OAuth2 PKCE authentication flow (`OAuthWorkflow`)

### Authentication Flow

The plugin uses OAuth2 with PKCE (Proof Key for Code Exchange) to authenticate with Koordinates:
1. Starts local HTTP server on port 8989
2. Opens browser to Koordinates OAuth endpoint
3. User authorizes, browser redirects to localhost
4. Exchanges code for access token
5. Retrieves API token for subsequent requests

Client IDs differ by platform (macOS vs others) - see `auth.py:61-64`.

### Kart Integration

Kart (https://kartproject.org/) is a separate QGIS plugin for versioned geospatial data. This plugin optionally integrates with Kart:
- Check if Kart plugin is available: `"kart" in qgis.utils.plugins`
- Clone operations delegated to `KartOperationManager` which creates `KartCloneTask` background tasks
- Tasks run via QGIS `QgsTask` system for async operations
- If Kart unavailable, raises `KartNotInstalledException`

### Qt and QGIS Integration

- Uses PyQt6 bindings (`from qgis.PyQt`)
- Main UI is a `QgsDockWidget` docked to QGIS main window
- Data browser items implement QGIS data item provider system (`QgsDataItemProvider`)
- Network requests use `QgsBlockingNetworkRequest` and `QgsNetworkAccessManager`

### Testing Strategy

Tests use unittest framework (not pytest as test framework, though pytest is used as runner):
- `koordinates/test_suite.py`: Test discovery and execution entry point
- Tests run inside QGIS environment (requires QGIS Python packages)
- Docker-based CI testing against multiple QGIS versions (3.22, 3.28, 3.30)
- Mock QGIS interface: `koordinates/test/qgis_interface.py`

## Code Style

- Black formatter with default settings
- Flake8 with max line length 99, ignoring E203
- Use type hints for new functions
- Prefer `type | None` over `Optional[type]` (modern Python syntax)

## Important Notes

- Plugin metadata is in `koordinates/metadata.txt` (version, QGIS min/max versions, etc.)
- Icons/images in `koordinates/icons/` and `koordinates/img/`
- UI files (.ui) in `koordinates/ui/` and loaded via `uic.loadUiType()`
- The plugin supports both Qt5 and Qt6 (QGIS 3.x and 4.x)
- External dependencies installed to `koordinates/extlibs/` via `helper.py setup`
