# C4 Context Diagram - Django Oscar E-commerce Platform

This diagram shows the system context - how Django Oscar fits into the broader environment and its interactions with external actors and systems.

```mermaid
C4Context
    title System Context Diagram for Django Oscar E-commerce Platform

    Person(customer, "Customer", "A person browsing and purchasing products online")
    Person(admin, "Store Administrator", "Manages products, orders, and store operations")
    Person(partner, "Partner/Fulfillment Manager", "Manages inventory and fulfills orders")

    System(oscar, "Django Oscar Platform", "E-commerce framework providing catalogue, basket, checkout, and order management")

    System_Ext(payment, "Payment Gateway", "Processes payments (e.g., PayPal, Stripe, Adyen)")
    System_Ext(shipping, "Shipping Provider", "Calculates shipping rates and handles logistics")
    System_Ext(search, "Search Engine", "Full-text search via Haystack (Elasticsearch, Solr, Whoosh)")
    System_Ext(email, "Email Service", "Sends transactional emails and notifications")
    System_Ext(analytics, "Analytics Platform", "Tracks user behavior and conversions")

    Rel(customer, oscar, "Browses products, adds to basket, places orders")
    Rel(admin, oscar, "Manages catalogue, views reports, processes orders")
    Rel(partner, oscar, "Manages stock levels, fulfills orders")

    Rel(oscar, payment, "Processes payments via")
    Rel(oscar, shipping, "Calculates shipping costs via")
    Rel(oscar, search, "Indexes and searches products via")
    Rel(oscar, email, "Sends notifications via")
    Rel(oscar, analytics, "Tracks events to")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Key Interactions

### Customer Interactions
- Browse product catalogue and categories
- Search for products
- Add products to basket/wishlist
- Complete checkout process
- View order history
- Write product reviews

### Administrator Interactions
- Manage product catalogue (products, categories, attributes)
- Configure offers, vouchers, and promotions
- Process and track orders
- Manage partners and stock levels
- Access analytics and reports via dashboard

### Partner/Fulfillment Interactions
- Update stock records
- View assigned orders
- Mark orders as shipped

### External System Integrations
- **Payment Gateways**: Multiple payment providers supported via extensions
- **Shipping Providers**: Custom shipping methods and rate calculations
- **Search Engines**: Haystack integration for Elasticsearch/Solr/Whoosh
- **Email Services**: Django email backend for transactional emails
- **Analytics**: Event tracking for user behavior and conversions
