# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django Oscar: a domain-driven e-commerce framework for Django, distributed as the `django-oscar` package (source in `src/oscar/`). Supported matrix (CI): Python 3.10–3.14, Django 4.2 / 5.2 / 6.0.

### Khafa project

This fork (Oscar 4.2.1) runs the khafa shop: the site is `sandbox/` (settings via env, Postgres, prod behind host nginx, see `docker-compose.prod.yml`). It is also the **backend of the Flutter mobile app** (`/workspace`), which is migrating here from WooCommerce:
- REST API via **django-oscar-api** 3.3 (DRF), mounted at `/api/` in `sandbox/urls.py`, **outside** `i18n_patterns`
- Mobile overrides in `sandbox/apps/api/` (`OSCARAPI_OVERRIDE_MODULES = ['apps.api']`): product list (paginated: `?page=`, `?page_size=`) and detail with inline price and availability, `?category=<id>` filter (descendants included), categories with `id`/`parent_id`/`has_children` and `?parent=<id>`
- Mobile auth: DRF token (`Authorization: Token <t>`) from `/api/auth/token/` (email as `username`, via `EmailBackend`); registration via `/api/register/` (`OSCARAPI_ENABLE_REGISTRATION`)
- API tests: `cd sandbox && ./manage.py test apps.api` (needs a writable `whoosh_index`, or `HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'` in a test settings module). If the API output changes, regenerate the Flutter fixtures in `/workspace/test/fixtures/oscar/`
- Deps: `djangorestframework` and `django-oscar-api` are in the `test` extra of `pyproject.toml` (installed by `make install`) and must be in `docker/prod/Dockerfile`
- Project-specific customisations go in `sandbox/` (`settings.py`, `urls.py`, `apps/`), not in `src/oscar/`
- Shares the Docker network `oscar` with the Flutter devcontainer (reachable there as `http://django-oscar:8000`)

## Commands

```bash
pip install -e .[test]          # install package + test deps
make install                    # also builds static assets (npm install && npm run build)

# Tests (pytest, settings module: tests.settings)
pytest                          # defaults to PostgreSQL (DATABASE_USER/PASSWORD/HOST/PORT env vars)
pytest --sqlite                 # use in-memory SQLite instead (no Postgres needed)
pytest --sqlite tests/integration/basket/test_models.py::TestClassName::test_name
pytest --lf                     # rerun failures
pytest --deprecation=strict     # turn deprecation/runtime warnings into errors

# Lint (what CI runs)
make lint                       # black --check + pylint on src/oscar and tests
make black                      # auto-format (migrations excluded)
npm run eslint                  # JS lint for src/oscar/static_src/oscar/js/oscar/

# Frontend assets (gulp: copies vendor libs and compiles SCSS from static_src → static)
npm run build
npm run watch

# Sandbox demo site (sandbox/, SQLite db, loads fixtures + catalogue CSVs)
make sandbox                    # install + build from scratch
sandbox/manage.py runserver

make test_migrations            # migration tests (sandbox/test_migrations.sh)
make docs                       # Sphinx docs in docs/
make extract_translations / compile_translations
```

## Architecture

**Forkable apps.** Each feature lives in `src/oscar/apps/<app>/` (catalogue, basket, checkout, order, offer, partner, shipping, payment, customer, voucher, wishlists, search, communication, analytics, address) plus `apps/dashboard/<sub-app>/`. Projects customise Oscar by "forking" an app (`oscar.core.customisation`, `oscar_fork_app` management command) and replacing the Oscar entry in `INSTALLED_APPS`. Everything in the codebase is written to support this, which drives these conventions:

- **Never import Oscar classes directly across apps.** Use `get_class("basket.forms", "AddToBasketForm")` / `get_classes(...)` from `oscar.core.loading`. The loader resolves the module against the app registry, so a forked app's module wins and falls back to the Oscar core module. Use `get_model("catalogue", "Product")` for models.
- **Models are split into `abstract_models.py` (all logic, `Abstract*` classes) and `models.py`** (concrete classes, each wrapped in `if not is_model_registered(app_label, "Name"):` so forks can override them). Put model changes in `abstract_models.py`; migrations live in each app's `migrations/`.
- **AppConfigs are `OscarConfig` subclasses** (`oscar.core.application`) that own their URLs: views are loaded via `get_class` in `ready()` and wired in `get_urls()`. `oscar.config.Shop` is the root config that mounts the sub-apps' URLs. Dashboard apps use `OscarDashboardConfig` with permission maps (`apps/dashboard/permissions.py`).
- Settings defaults are in `src/oscar/defaults.py` (`OSCAR_*`); `OSCAR_DYNAMIC_CLASS_LOADER` makes the class loader itself replaceable.

**Key domain pieces:** pricing/availability strategies in `apps/partner/strategy.py` (a strategy is attached to each request/basket and selects stockrecords); offers/conditions/benefits in `apps/offer/` with the applicator applying them to baskets; checkout session and order placement in `apps/checkout/` (`mixins.OrderPlacementMixin`) and `apps/order/utils.OrderCreator`; order status pipelines and event processing in `apps/order/processing.py`. Search uses django-haystack (Whoosh in tests, Solr/Elasticsearch in production setups).

**Templates and static:** templates in `src/oscar/templates/oscar/`; SCSS/JS source in `src/oscar/static_src/` (built output under `src/oscar/static/` is generated, not edited).

**Tests** (`tests/`): split into `unit/`, `integration/` and `functional/` (WebTest-based, e.g. `oscar.test.testcases.WebTestCase`). `tests/_site/` contains a test project including forked apps (`tests/_site/apps/`) used to exercise the customisation machinery. Reusable factories and helpers ship in `src/oscar/test/` (`factories`, `basket`, `testcases`).

## Style

- black formatting; pylint config in `pylintrc` (code often uses targeted `# pylint: disable=...` comments). flake8/isort settings in `setup.cfg`.
- User-facing strings are translated with `gettext_lazy as _`.
