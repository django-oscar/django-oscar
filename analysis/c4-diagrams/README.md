# Django Oscar C4 Architecture Diagrams

This directory contains C4 model diagrams for the Django Oscar e-commerce platform, rendered in Mermaid.js format.

## What is C4?

The C4 model provides a way to describe and communicate software architecture at different levels of abstraction:

- **Level 1 - Context**: Shows the system in its environment with users and external systems
- **Level 2 - Container**: Shows the high-level technology choices and how the system is decomposed
- **Level 3 - Component**: Zooms into a container to show internal components
- **Level 4 - Code** (not included): Shows implementation details like classes

## Diagrams in this Directory

1. **[01-context-diagram.md](01-context-diagram.md)** - System Context
   - Shows Django Oscar's place in the broader ecosystem
   - External actors: Customers, Admins, Partners
   - External systems: Payment gateways, Search engines, Email services

2. **[02-container-diagram.md](02-container-diagram.md)** - Container View
   - Shows technology stack
   - Web application, Dashboard, REST API, Database, Cache, Search
   - How containers communicate

3. **[03-component-diagram.md](03-component-diagram.md)** - Component View
   - Zooms into the Django web application
   - Shows Oscar's internal apps and their relationships
   - Key components: Catalogue, Basket, Checkout, Order, Partner, Offer, etc.

4. **[04-domain-model-diagram.md](04-domain-model-diagram.md)** - Domain Model
   - Entity-Relationship diagram of core domain
   - Shows aggregates: Catalogue, Basket, Order, Partner, Offer, Payment
   - Key business entities and their relationships

## How to View the Diagrams

### In GitHub
GitHub natively renders Mermaid diagrams in Markdown files. Simply click on any diagram file to view it.

### In VS Code
Install the [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) extension.

### In Other Editors
- Copy the Mermaid code blocks
- Paste into the [Mermaid Live Editor](https://mermaid.live/)
- Or use any Mermaid-compatible tool

## Key Architectural Insights

### Dynamic Class Loading
Oscar's defining architectural feature is its **dynamic class loading system** (`get_class()`), which allows any component to be customized without forking:

```python
from oscar.core.loading import get_class

ProductForm = get_class('catalogue.forms', 'ProductForm')
```

This looks for `ProductForm` in:
1. Your local forked app (if exists)
2. Oscar's core implementation (fallback)

### App-Based Modularity
Oscar is organized into discrete Django apps, each representing a domain:
- **catalogue** - Product catalog management
- **basket** - Shopping cart
- **checkout** - Purchase flow
- **order** - Order management
- **partner** - Fulfillment and inventory
- **offer** - Promotions and discounts
- **voucher** - Coupon codes
- **payment** - Payment processing
- **customer** - User accounts

### Extensibility Patterns
1. **Abstract Base Models** - All models inherit from Abstract* classes
2. **Signal-Based Events** - Key business events emit Django signals
3. **Strategy Pattern** - Pricing, availability, shipping use strategies
4. **Template Overriding** - Standard Django template inheritance
5. **Settings-Based Config** - All settings prefixed with `OSCAR_*`

### Domain-Driven Design
Oscar follows DDD principles:
- **Aggregates**: Product, Basket, Order, Offer
- **Value Objects**: Prices, Addresses
- **Entities**: Product, Order, User
- **Domain Events**: Signals for state changes
- **Bounded Contexts**: Each app has its own domain

## Navigation Guide

**Start here if you want to understand:**

- **Overall system context** → [Context Diagram](01-context-diagram.md)
- **Technology stack** → [Container Diagram](02-container-diagram.md)
- **Internal architecture** → [Component Diagram](03-component-diagram.md)
- **Data model and relationships** → [Domain Model](04-domain-model-diagram.md)

## Additional Resources

- [CLAUDE.md](../../CLAUDE.md) - Development guide for this codebase
- [Django Oscar Documentation](https://django-oscar.readthedocs.io/)
- [C4 Model](https://c4model.com/) - Learn more about C4 diagrams
- [Mermaid.js](https://mermaid.js.org/) - Diagramming syntax reference
