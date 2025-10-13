# Django Oscar Architecture Overview

This document provides a comprehensive overview of the Django Oscar e-commerce platform architecture. For development workflows and commands, see [CLAUDE.md](CLAUDE.md).

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Architectural Principles](#core-architectural-principles)
3. [Architecture Diagrams](#architecture-diagrams)
4. [Technology Stack](#technology-stack)
5. [Domain Model](#domain-model)
6. [Key Design Patterns](#key-design-patterns)
7. [Customization and Extension](#customization-and-extension)
8. [Data Flow](#data-flow)
9. [Integration Points](#integration-points)

---

## System Overview

Django Oscar is a **domain-driven e-commerce framework** for Django, designed with customization and flexibility as core principles. Rather than being a monolithic application, Oscar is a collection of loosely-coupled Django apps that work together to provide complete e-commerce functionality.

### Key Characteristics

- **Framework, not application**: Oscar provides building blocks, not a finished product
- **Customization-first**: Every component can be overridden without forking
- **Domain-driven design**: Organized around business domains (catalogue, basket, order, etc.)
- **Django-native**: Leverages Django's patterns and ecosystem
- **Production-ready**: Powers major e-commerce sites worldwide

### Supported Versions

- Python 3.8+
- Django 4.2+
- Current LTS: 3.2 (supported until January 2026)

---

## Core Architectural Principles

### 1. Dynamic Class Loading

Oscar's defining architectural feature is the **dynamic class loading system**, implemented via `get_class()`. This enables customization without forking the framework.

```python
from oscar.core.loading import get_class

ProductForm = get_class('catalogue.forms', 'ProductForm')
```

**Resolution order:**
1. Your local forked app (if exists)
2. Oscar's core implementation (fallback)

This pattern is used throughout Oscar for views, forms, models, utilities, and more.

**Implementation**: See `src/oscar/core/loading.py`

### 2. App-Based Modularity

Oscar is organized into discrete Django apps, each representing a **bounded context** in domain-driven design:

| App | Domain | Primary Responsibility |
|-----|--------|----------------------|
| `catalogue` | Product Catalog | Products, categories, attributes, reviews |
| `basket` | Shopping Cart | Cart management, line items, voucher application |
| `checkout` | Purchase Flow | Multi-step checkout, address/shipping/payment |
| `order` | Order Management | Order placement, tracking, fulfillment |
| `partner` | Fulfillment | Partners, stock records, availability |
| `offer` | Promotions | Conditional offers, discounts, rules |
| `voucher` | Coupons | Voucher codes, redemption tracking |
| `payment` | Payment Processing | Payment sources, transactions, gateways |
| `shipping` | Shipping | Shipping methods, cost calculation |
| `customer` | User Accounts | Registration, profiles, order history |
| `address` | Address Management | User addresses, validation |
| `search` | Product Search | Haystack integration for full-text search |
| `wishlists` | Wishlists | Product wish lists |
| `analytics` | Analytics | Event tracking, reporting |
| `communication` | Notifications | Email templates, notifications |
| `dashboard` | Admin Interface | Staff-facing admin dashboard |

### 3. Abstract Base Models

All Oscar models inherit from `Abstract*` classes, enabling customization:

```python
# oscar/apps/catalogue/abstract_models.py
class AbstractProduct(models.Model):
    # Core product definition
    class Meta:
        abstract = True

# oscar/apps/catalogue/models.py
class Product(AbstractProduct):
    pass  # Can be overridden in your project
```

This pattern allows you to add fields, methods, or override behavior without modifying Oscar's code.

### 4. Signal-Based Events

Oscar emits Django signals for key business events:

- `basket_addition` - Product added to basket
- `order_placed` - Order successfully created
- `order_status_changed` - Order status updated
- `user_registered` - New user account
- `product_viewed` - Product page viewed
- `product_search` - Search performed

Signals enable decoupled event handling and extensibility.

### 5. Strategy Pattern

Oscar uses the Strategy pattern for behavior that varies by context:

- **Availability strategies**: How to calculate product availability
- **Pricing strategies**: How to determine prices
- **Shipping methods**: How to calculate shipping costs
- **Payment sources**: How to process payments

Strategies are configurable via Django settings.

---

## Architecture Diagrams

Detailed architecture diagrams are available in the `analysis/c4-diagrams/` directory, using the C4 model:

### [Level 1: Context Diagram](analysis/c4-diagrams/01-context-diagram.md)
Shows Oscar in its broader ecosystem:
- **Actors**: Customers, Administrators, Partners
- **External Systems**: Payment gateways, shipping providers, search engines, email services

### [Level 2: Container Diagram](analysis/c4-diagrams/02-container-diagram.md)
Shows the technology stack:
- **Django Web Application**: Main application
- **Dashboard**: Admin interface
- **REST API**: Optional API layer
- **Database**: PostgreSQL/MySQL
- **Cache**: Redis/Memcached
- **Search Engine**: Elasticsearch/Solr

### [Level 3: Component Diagram](analysis/c4-diagrams/03-component-diagram.md)
Shows internal app structure and relationships:
- All Oscar apps and their interactions
- Data flow between components
- Integration points

### [Level 4: Domain Model](analysis/c4-diagrams/04-domain-model-diagram.md)
Shows the core domain entities and relationships:
- **Aggregates**: Product, Basket, Order, Partner, Offer
- **Value Objects**: Price, Address, LinePrice
- **Entities**: Product, Order, User, StockRecord

---

## Technology Stack

### Core Framework
- **Django 4.2+**: Web framework
- **Python 3.8+**: Programming language

### Frontend
- **Bootstrap 4.6.2**: UI framework
- **jQuery 3.7.1**: DOM manipulation
- **Select2**: Enhanced select elements
- **TinyMCE**: Rich text editor
- **SCSS**: Styling (compiled to CSS)

### Database
- **PostgreSQL** (recommended): Primary database
- **MySQL/MariaDB**: Alternative option
- **SQLite**: Development only

### Search
- **Haystack**: Search abstraction layer
- **Elasticsearch** (recommended): Search engine
- **Solr**: Alternative search engine
- **Whoosh**: Simple Python-based search

### Caching
- **Redis** (recommended): Cache and sessions
- **Memcached**: Alternative cache backend
- **Database**: Fallback cache

### Asset Management
- **Gulp**: Build tool
- **Webpack**: Optional bundler
- **npm**: Package management

### Testing
- **pytest**: Test runner
- **pytest-django**: Django integration
- **factory-boy**: Test data generation
- **WebTest**: Integration testing
- **coverage**: Code coverage

---

## Domain Model

### Core Aggregates

#### 1. Catalogue Aggregate
**Root**: `Product`

```
Product
├── ProductClass (defines attributes)
├── ProductAttribute (flexible metadata)
├── ProductImage
├── ProductRecommendation
├── Category (hierarchical tree)
└── StockRecord (from Partner aggregate)
```

**Key concepts:**
- Products can have parent-child relationships (variants)
- Categories use django-treebeard for hierarchical structure
- Product classes define available attributes
- Reviews are separate entities linked to products

#### 2. Basket Aggregate
**Root**: `Basket`

```
Basket
├── Line (basket items)
│   ├── LineAttribute
│   └── Product reference
├── Applied Vouchers
└── Applied Offers
```

**Key concepts:**
- Baskets can be anonymous or user-owned
- Baskets merge on user login
- Lines track individual discounts
- Baskets freeze during checkout

#### 3. Order Aggregate
**Root**: `Order`

```
Order
├── Line (order line items)
│   └── LinePrice
├── ShippingAddress
├── BillingAddress
├── PaymentEvent
├── ShippingEvent
├── Discount
└── Surcharge
```

**Key concepts:**
- Orders are immutable once placed
- Events provide audit trail
- Status changes trigger signals
- Order numbers are unique and configurable

#### 4. Partner Aggregate
**Root**: `Partner`

```
Partner
├── StockRecord (per product)
│   ├── Stock level
│   ├── Price
│   └── Partner SKU
└── Availability strategy
```

**Key concepts:**
- Multiple partners can stock same product
- Each partner sets their own prices
- Availability calculated via strategies
- Stock allocation happens on order placement

#### 5. Offer Aggregate
**Root**: `ConditionalOffer`

```
ConditionalOffer
├── Condition (when to apply)
│   └── Range (which products)
├── Benefit (what discount)
└── Voucher (optional trigger)
```

**Key concepts:**
- Offers are rule-based discount engine
- Conditions check basket state
- Benefits modify basket pricing
- Offers can be exclusive or combinable

### Entity Relationships

```
Customer → creates → Order
Order → contains → Product (via Line)
Product → has → StockRecord → owned by → Partner
Basket → applies → Offer
Basket → redeems → Voucher → grants → Offer
Order → triggers → PaymentEvent
Order → triggers → ShippingEvent
Product → belongs to → Category
Product → has → ProductClass → defines → ProductAttribute
```

---

## Key Design Patterns

### 1. Dynamic Class Loading
**Pattern**: Service Locator + Template Method

Enables customization without inheritance or monkey-patching.

**Usage:**
```python
# Instead of direct import
# from oscar.apps.catalogue.views import ProductDetailView

# Use dynamic loading
ProductDetailView = get_class('catalogue.views', 'ProductDetailView')
```

### 2. Abstract Base Models
**Pattern**: Template Method + Inheritance

All models use abstract base classes:
```python
from oscar.apps.catalogue.abstract_models import AbstractProduct

class Product(AbstractProduct):
    # Add custom fields or override methods
    custom_field = models.CharField(max_length=100)
```

### 3. Application Class Pattern
**Pattern**: Composition + Configuration

Each app has an `Application` class that wires together URLs, views, and permissions:

```python
# oscar/apps/catalogue/app.py
class CatalogueApplication(OscarConfig):
    name = 'oscar.apps.catalogue'

    def ready(self):
        # Register signal handlers, etc.
        pass

    def get_urls(self):
        # Return URL patterns
        pass
```

### 4. Strategy Pattern
**Pattern**: Strategy + Dependency Injection

Used for variable behavior:

```python
# Availability strategy
class Unavailable(Base):
    def is_available_to_buy(self, stockrecord):
        return False, "Unavailable"

# Configured via settings
OSCAR_AVAILABILITY_STRATEGY = 'myproject.availability.AlwaysAvailable'
```

### 5. Signal-Based Events
**Pattern**: Observer

Decouple components via Django signals:

```python
from oscar.apps.order.signals import order_placed

@receiver(order_placed)
def handle_order_placed(sender, order, user, **kwargs):
    # Send confirmation email, update inventory, etc.
    pass
```

### 6. Form Mixins
**Pattern**: Mixin + Composition

Forms use mixins for common functionality:
```python
class BasketLineForm(SingleProductMixin, BaseBasketLineForm):
    # Compose functionality from mixins
    pass
```

### 7. View Mixins
**Pattern**: Mixin + Class-Based Views

Views use Django's CBV pattern with Oscar-specific mixins:
```python
class ProductDetailView(DetailView):
    # Uses Django's DetailView
    # Extended with Oscar mixins
    pass
```

---

## Customization and Extension

### Method 1: Forking an App

**When to use**: Customize models, views, forms, or templates

**Steps:**
1. Fork the app:
   ```bash
   python manage.py oscar_fork_app catalogue myproject/catalogue
   ```

2. Add to `INSTALLED_APPS` **before** Oscar's app:
   ```python
   INSTALLED_APPS = [
       'myproject.catalogue',  # Your fork
       # ... other apps
   ]
   ```

3. Customize in your forked app:
   ```python
   # myproject/catalogue/models.py
   from oscar.apps.catalogue.abstract_models import AbstractProduct

   class Product(AbstractProduct):
       video_url = models.URLField(blank=True)
   ```

4. Run migrations:
   ```bash
   python manage.py makemigrations catalogue
   python manage.py migrate
   ```

### Method 2: Overriding Templates

**When to use**: Change UI without forking

**Steps:**
1. Create template in your project with same path:
   ```
   templates/oscar/catalogue/detail.html
   ```

2. Oscar's template loader finds your version first

### Method 3: Settings Configuration

**When to use**: Configure behavior without code changes

**Common settings:**
```python
# Oscar settings (in settings.py)
OSCAR_HOMEPAGE = '/'
OSCAR_SHOP_NAME = 'My Store'
OSCAR_DEFAULT_CURRENCY = 'USD'
OSCAR_ALLOW_ANON_CHECKOUT = True
OSCAR_INITIAL_ORDER_STATUS = 'Pending'
```

See `src/oscar/defaults.py` for all settings.

### Method 4: Signal Handlers

**When to use**: React to events without modifying code

**Example:**
```python
from django.dispatch import receiver
from oscar.apps.order.signals import order_placed

@receiver(order_placed)
def send_to_warehouse(sender, order, **kwargs):
    # Custom order handling
    warehouse_api.create_fulfillment(order)
```

### Method 5: Strategy Classes

**When to use**: Customize availability, pricing, shipping

**Example:**
```python
# myproject/availability.py
from oscar.apps.partner.strategy import Base

class CustomAvailability(Base):
    def availability_policy(self, product, stockrecord):
        # Custom logic
        return Unavailable()

# settings.py
OSCAR_AVAILABILITY_STRATEGY = 'myproject.availability.CustomAvailability'
```

---

## Data Flow

### Customer Purchase Flow

```
1. Browse Products
   └─> Catalogue App
       └─> Search App (optional)

2. Add to Basket
   └─> Basket App
       ├─> Check Availability (Partner App)
       ├─> Apply Offers (Offer App)
       └─> Apply Vouchers (Voucher App)

3. Checkout
   └─> Checkout App
       ├─> Validate Address (Address App)
       ├─> Calculate Shipping (Shipping App)
       ├─> Process Payment (Payment App)
       └─> Create Order (Order App)

4. Order Placement
   └─> Order App
       ├─> Allocate Stock (Partner App)
       ├─> Record Payment (Payment App)
       ├─> Send Confirmation (Communication App)
       └─> Track Event (Analytics App)

5. Order Fulfillment
   └─> Dashboard (Partner/Staff)
       ├─> Update Order Status
       ├─> Record Shipping Event
       └─> Send Tracking Email
```

### Admin Product Management Flow

```
1. Create Product
   └─> Dashboard / Catalogue App
       ├─> Define Product Class
       ├─> Set Attributes
       ├─> Upload Images
       └─> Assign Categories

2. Manage Inventory
   └─> Dashboard / Partner App
       ├─> Create Stock Records
       ├─> Set Prices
       └─> Update Stock Levels

3. Configure Promotions
   └─> Dashboard / Offer App
       ├─> Define Conditions
       ├─> Set Benefits
       └─> Create Vouchers (optional)
```

---

## Integration Points

### Payment Gateways

Oscar provides a gateway-agnostic payment abstraction. Integration requires:

1. **Payment source**: Record payment method
2. **Transaction**: Log payment attempts
3. **Payment event**: Audit trail

**Popular integrations:**
- [django-oscar-paypal](https://github.com/django-oscar/django-oscar-paypal)
- [django-oscar-adyen](https://github.com/oscaro/django-oscar-adyen)
- Custom integrations via Payment App

### Search Engines

Oscar uses Haystack for search abstraction:

```python
# settings.py
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'oscar',
    },
}
```

**Supported engines:**
- Elasticsearch (recommended)
- Solr
- Whoosh (development only)

### REST API

Oscar doesn't include a built-in API but provides:
- [django-oscar-api](https://github.com/django-oscar/django-oscar-api): RESTful API using Django REST Framework

### Analytics

Oscar emits events that can be tracked:

```python
from oscar.apps.analytics import receivers

# Automatically tracks:
# - Product views
# - User searches
# - User registrations
```

Integrate with:
- Google Analytics
- Segment
- Mixpanel
- Custom analytics platforms

---

## Additional Resources

- **Development Guide**: [CLAUDE.md](CLAUDE.md) - Commands and workflows
- **C4 Architecture Diagrams**: [analysis/c4-diagrams/](analysis/c4-diagrams/)
- **Official Documentation**: [django-oscar.readthedocs.io](https://django-oscar.readthedocs.io/)
- **Source Code**: `src/oscar/` - Well-documented codebase
- **Tests**: `tests/` - Extensive test suite with examples

---

## Quick Reference

### Common Patterns

```python
# Dynamic class loading
ProductForm = get_class('catalogue.forms', 'ProductForm')

# Model customization
from oscar.apps.catalogue.abstract_models import AbstractProduct
class Product(AbstractProduct):
    custom_field = models.CharField(max_length=100)

# Signal handling
from oscar.apps.order.signals import order_placed
@receiver(order_placed)
def handle_order(sender, order, **kwargs):
    pass

# Strategy configuration
OSCAR_AVAILABILITY_STRATEGY = 'myproject.availability.CustomStrategy'
```

### File Locations

- **Core code**: `src/oscar/apps/`
- **Templates**: `src/oscar/templates/oscar/`
- **Static assets**: `src/oscar/static/oscar/`
- **Tests**: `tests/`
- **Sandbox**: `sandbox/` (demo site)
- **Docs**: `docs/source/`

---

**Last Updated**: 2025-01-13
**Oscar Version**: 3.2 LTS
