# C4 Container Diagram - Django Oscar E-commerce Platform

This diagram shows the high-level technology choices and how the system is decomposed into containers (applications, databases, file systems, etc.).

```mermaid
C4Container
    title Container Diagram for Django Oscar E-commerce Platform

    Person(customer, "Customer", "Browses and purchases products")
    Person(admin, "Store Admin", "Manages store operations")
    Person(partner, "Partner", "Manages inventory")

    Container_Boundary(oscar_system, "Django Oscar Platform") {
        Container(web_app, "Web Application", "Django/Python", "Serves HTML pages, handles HTTP requests, business logic")
        Container(dashboard, "Dashboard App", "Django/Python", "Admin interface for store management")
        Container(api, "REST API", "Django REST Framework", "RESTful API endpoints (via django-oscar-api extension)")

        ContainerDb(db, "Database", "PostgreSQL/MySQL/SQLite", "Stores products, orders, customers, inventory")
        ContainerDb(cache, "Cache", "Redis/Memcached", "Session data, cached queries, basket data")

        Container(static_files, "Static Assets", "JavaScript/CSS/Images", "Bootstrap 4, jQuery, Select2, TinyMCE")
        Container(media_files, "Media Storage", "File System/S3", "Product images, user uploads")

        Container(task_queue, "Task Queue", "Celery (optional)", "Background jobs for email, exports, reports")
    }

    System_Ext(search_engine, "Search Index", "Elasticsearch/Solr/Whoosh", "Full-text product search")
    System_Ext(payment_gateway, "Payment Gateway", "External API", "Payment processing")
    System_Ext(email_service, "Email Service", "SMTP/SendGrid/SES", "Transactional emails")

    Rel(customer, web_app, "Browses products, places orders", "HTTPS")
    Rel(admin, dashboard, "Manages store", "HTTPS")
    Rel(customer, api, "Mobile/SPA interaction", "HTTPS/JSON")
    Rel(partner, dashboard, "Manages inventory", "HTTPS")

    Rel(web_app, db, "Reads/writes data", "SQL")
    Rel(dashboard, db, "Reads/writes data", "SQL")
    Rel(api, db, "Reads/writes data", "SQL")

    Rel(web_app, cache, "Stores sessions/baskets", "Redis Protocol")
    Rel(web_app, static_files, "Serves assets")
    Rel(web_app, media_files, "Serves images")

    Rel(web_app, search_engine, "Indexes/searches products", "HTTP/JSON")
    Rel(web_app, payment_gateway, "Processes payments", "HTTPS")
    Rel(web_app, task_queue, "Queues background jobs", "AMQP/Redis")
    Rel(task_queue, email_service, "Sends emails", "SMTP")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Container Details

### Web Application (Django)
- **Technology**: Python 3.8+, Django 4.2+
- **Responsibilities**:
  - Product catalogue rendering
  - Basket/cart management
  - Checkout flow orchestration
  - Order placement and tracking
  - Customer account management
  - Offer/voucher application
- **Key Apps**: catalogue, basket, checkout, order, customer, offer, voucher, payment, shipping

### Dashboard Application
- **Technology**: Django admin-like interface with Bootstrap 4
- **Responsibilities**:
  - Product and category management
  - Order processing and fulfillment
  - Customer management
  - Reporting and analytics
  - Partner management
  - Offer and voucher configuration
- **Access Control**: Permission-based, can be scoped to specific partners

### REST API (Optional Extension)
- **Technology**: Django REST Framework
- **Extension**: django-oscar-api
- **Responsibilities**:
  - Headless/mobile commerce
  - Third-party integrations
  - SPA (Single Page Application) backend

### Database
- **Primary Options**: PostgreSQL (recommended), MySQL, SQLite (dev only)
- **Schema**:
  - Products and catalogue structure
  - Customer and order data
  - Stock records and partner info
  - Offers, vouchers, and discounts
  - Analytics events

### Cache Layer
- **Technologies**: Redis (recommended), Memcached, Local Memory
- **Uses**:
  - Session storage
  - Basket data (temporary)
  - Query result caching
  - Product availability checks

### Static & Media Files
- **Static**: Bootstrap, jQuery, Select2, TinyMCE, custom CSS/JS
- **Media**: Product images, category images, user uploads
- **Build Process**: Gulp for SCSS compilation and asset copying
- **Storage**: Local filesystem or cloud storage (S3, etc.)

### Search Engine
- **Integration**: Django Haystack
- **Backends**: Elasticsearch, Solr, Whoosh (development)
- **Indexed Data**: Product titles, descriptions, attributes, SKUs

### Task Queue (Optional)
- **Technology**: Celery with Redis/RabbitMQ
- **Common Tasks**:
  - Email sending
  - Report generation
  - Data exports
  - Batch operations
