# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Oscar is a domain-driven e-commerce framework for Django. It's designed with customization in mind - any part of the core functionality can be overridden to suit specific project needs.

**Key Concept**: Oscar supports Django 4.2+ and Python 3.8+. The current LTS version is 3.2 (supported until January 2026).

## Essential Commands

### Installation & Setup
```bash
# Install for local development
make install

# Create virtual environment with all dependencies
make venv

# Install and build sandbox (demo site)
make sandbox

# Clean and rebuild sandbox from scratch
make build_sandbox
```

### Running the Sandbox
```bash
# Run the development server
sandbox/manage.py runserver

# The sandbox uses settings.py by default
# For PostgreSQL: Use sandbox/settings_postgres.py
```

### Testing
```bash
# Run all tests
make test

# Run tests with pytest directly (after venv is created)
venv/bin/py.test

# Run specific test file
venv/bin/py.test tests/unit/catalogue/test_models.py

# Run specific test
venv/bin/py.test tests/unit/catalogue/test_models.py::TestProduct::test_method_name

# Re-run only failed tests
make retest

# Generate coverage report
make coverage

# Test migrations
make test_migrations
```

### Code Quality
```bash
# Run linting (black + pylint)
make lint

# Auto-format code with black
make black

# Build frontend assets
npm run build

# Watch and rebuild assets on changes
npm run watch

# Run ESLint on JavaScript
npm run eslint
```

### Translations
```bash
# Extract translatable strings
make extract_translations

# Compile translation files
make compile_translations
```

### Documentation
```bash
# Build documentation
make docs
```

## Architecture Overview

### Dynamic Class Loading System

Oscar's core architectural pattern is **dynamic class loading**, which enables customization without forking the framework.

**Key function**: `get_class(module_label, classname, module_prefix="oscar.apps")`

Example:
```python
from oscar.core.loading import get_class

ProductForm = get_class('catalogue.forms', 'ProductForm')
```

This searches for the class in:
1. Your local app (if you've forked the app)
2. Oscar's core implementation (fallback)

This allows you to override any class (views, forms, models, etc.) by creating a local version.

### App Structure

Oscar is organized into Django apps under `src/oscar/apps/`:

- **catalogue** - Products, categories, product classes, attributes
- **partner** - Stock records, partner/fulfillment management
- **basket** - Shopping basket/cart functionality
- **order** - Order processing and management
- **checkout** - Checkout flow and payment
- **payment** - Payment handling
- **shipping** - Shipping methods and calculations
- **offer** - Promotional offers and discounts
- **voucher** - Voucher/coupon functionality
- **customer** - Customer accounts and profiles
- **address** - Address management
- **analytics** - Analytics tracking
- **dashboard** - Admin dashboard (has many sub-apps)
- **search** - Search integration (uses Haystack)
- **wishlists** - Wishlist functionality
- **communication** - Email notifications

### Model Patterns

Oscar uses abstract base models to enable customization:

```python
# In oscar/apps/catalogue/abstract_models.py
class AbstractProduct(models.Model):
    # Core product model definition
    class Meta:
        abstract = True

# In oscar/apps/catalogue/models.py
from oscar.apps.catalogue.abstract_models import *

if not is_model_registered('catalogue', 'Product'):
    class Product(AbstractProduct):
        pass
```

To customize a model, fork the app and override the concrete model class.

### URL Configuration

The main Shop app (`oscar.config.Shop`) aggregates URLs from all sub-apps:

```python
# From src/oscar/config.py
def get_urls(self):
    urls = [
        path('catalogue/', self.catalogue_app.urls),
        path('basket/', self.basket_app.urls),
        # ... etc
    ]
    return urls
```

Include in your project's urls.py:
```python
from oscar.app import application
urlpatterns = [
    path('', application.urls),
]
```

### Frontend Assets

Frontend assets are built with Gulp and use:
- **Bootstrap 4.6.2** - UI framework
- **jQuery 3.7.1** - DOM manipulation
- **Select2** - Enhanced select elements
- **TinyMCE** - Rich text editor
- **SCSS** - Compiled to CSS

Source files: `src/oscar/static_src/oscar/`
Built files: `src/oscar/static/oscar/` (generated)

### Sandbox Application

The `sandbox/` directory contains a complete demo Oscar site used for:
- Development and testing
- Examples of Oscar usage
- Docker deployments

It includes fixtures for products, orders, and users (username: `superuser`, password: `testing`).

## Customization Patterns

### Forking an App

To customize Oscar functionality:

1. Create a local app with the same name:
```bash
python manage.py oscar_fork_app catalogue myproject/catalogue
```

2. Add to `INSTALLED_APPS` before Oscar's version:
```python
INSTALLED_APPS = [
    'myproject.catalogue',  # Your fork
    # ... other apps
]
```

3. Override specific classes in your forked app

### Settings

Oscar settings are prefixed with `OSCAR_*`. Key settings:
- `OSCAR_HOMEPAGE` - URL for the homepage redirect
- `OSCAR_DYNAMIC_CLASS_LOADER` - Class loading function (default: `oscar.core.loading.default_class_loader`)
- See `src/oscar/defaults.py` for all Oscar settings

## Testing Conventions

- Tests are in `tests/` directory, organized by app and type (`unit/`, `integration/`, `functional/`)
- Use `pytest` with `django-webtest` for integration tests
- Use `factory-boy` for test data (factories in `oscar.test.factories`)
- Test settings: `tests/settings.py`
- Configuration: `setup.cfg` (pytest section)

## Important Files

- `src/oscar/defaults.py` - All default Oscar settings
- `src/oscar/core/loading.py` - Dynamic class loading implementation
- `src/oscar/config.py` - Main Oscar app configuration
- `pyproject.toml` - Package dependencies and metadata
- `Makefile` - Development task automation
