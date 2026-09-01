# E-Commerce Project

A Django-based e-commerce application for browsing products, managing a customer cart, placing orders, and completing online payments. It includes customer profiles, product categories and inventory, order history, ratings, invoice downloads, email tasks, and a Cashfree payment checkout integration.

The application uses SQLite for local development and stores uploaded product images under `media/`.

## Tech stack

- Python and Django
- SQLite
- Cashfree Payment Gateway
- Celery with Redis (background tasks)
- Bootstrap templates, ReportLab, and Pillow

## Database schema design

Django's built-in `auth.User` model provides authentication. The `Customer` model extends it with contact and address details.

```mermaid
erDiagram
    AUTH_USER ||--|| CUSTOMER : "has profile"
    CATEGORY ||--o{ PRODUCT : contains
    CUSTOMER ||--|| CART : owns
    CART ||--o{ CART_ITEM : contains
    PRODUCT ||--o{ CART_ITEM : added_as
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--o{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : ordered_as
    ORDER ||--o{ PAYMENT : records
    CUSTOMER ||--o{ RATING : gives
    PRODUCT ||--o{ RATING : receives

    AUTH_USER {
        int id PK
        string username
        string email
    }
    CUSTOMER {
        int id PK
        int user_id FK
        string email
        string phone UK
        text address
    }
    CATEGORY {
        int id PK
        string name
    }
    PRODUCT {
        int id PK
        string title
        string title_kn
        text description
        decimal price
        int stock
        string product_image
        int category_id FK
    }
    CART {
        int id PK
        int customer_id FK
        datetime created_at
    }
    CART_ITEM {
        int id PK
        int cart_id FK
        int product_id FK
        int quantity
    }
    ORDER {
        int id PK
        int customer_id FK
        text shipping_address
        string phone
        string status
        datetime created_at
    }
    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        decimal price
        int quantity
    }
    PAYMENT {
        int id PK
        int order_id FK
        string cashfree_order_id
        string cashfree_payment_id
        string status
        decimal amount
        datetime created_at
    }
    RATING {
        int id PK
        int customer_id FK
        int product_id FK
        int rating
    }
```

Key rules:

- A customer has one cart; a cart can contain many items.
- A product can appear only once per cart (`cart`, `product` is unique).
- Checkout snapshots the current product price into each `OrderItem` and reserves stock inside a database transaction.
- Orders move through `PENDING`, `PAID`, `SHIPPED`, `DELIVERED`, or `CANCELED`; payments track `CREATED`, `PENDING`, `SUCCESS`, or `FAILED`.

## Directory tree

```text
.
├── manage.py                    # Django management entry point
├── requirements.txt             # Python dependencies
├── ecommerce/                   # Project configuration
│   ├── settings.py              # Database, Cashfree, email, Celery settings
│   ├── urls.py                  # Root URL routes
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
├── store/                       # Main e-commerce application
│   ├── models.py                # Catalog, cart, order, payment, and rating models
│   ├── views.py                 # Storefront, checkout, and payment logic
│   ├── urls.py                  # Application routes
│   ├── forms.py
│   ├── tasks.py                 # Celery tasks
│   ├── admin.py
│   ├── context_processors.py
│   ├── migrations/              # Database migrations
│   └── management/commands/     # `create_data` command
├── templates/                   # Django HTML templates
├── static/                      # Stylesheet and static images
└── media/                       # Uploaded product images
```

## Payment gateway flow

The project integrates Cashfree's JavaScript checkout in sandbox mode by default.

```mermaid
sequenceDiagram
    actor Customer
    participant App as Django app
    participant DB as SQLite database
    participant Cashfree as Cashfree API / Checkout

    Customer->>App: Submit checkout form
    App->>DB: Lock products, create Order and OrderItems
    App->>DB: Decrement reserved stock
    App-->>Customer: Redirect to /payment/{order_id}/
    App->>Cashfree: Create Cashfree order (amount and customer details)
    Cashfree-->>App: cashfree order ID + payment session ID
    App->>DB: Create/update Payment as PENDING
    App-->>Customer: Render checkout with payment session ID
    Customer->>Cashfree: Complete payment in Cashfree checkout
    Cashfree-->>App: Redirect to /payment/return/?order_id=...
    App->>Cashfree: Fetch order status server-side
    alt Cashfree status is PAID
        App->>DB: Mark Payment SUCCESS and Order PAID
        App->>DB: Clear the customer's cart
        App-->>Customer: Show order success page
    else Status is FAILED or CANCELLED
        App->>DB: Mark Payment FAILED
        App-->>Customer: Show payment failure page and retry option
    else Status is pending
        App-->>Customer: Show processing message
    end
```

[Visualized ER diagram](https://miro.com/app/board/uXjVHR8FjBo=/?moveToWidget=3458764682282786316&cot=14)

Required environment variables are loaded from `.env`:

```env
SECRET_KEY=your-django-secret-key
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
# Optional; defaults are shown below.
CASHFREE_API_VERSION=2025-01-01
CASHFREE_BASE_URL=https://sandbox.cashfree.com/pg
EMAIL_HOST_USER=your-email-address
EMAIL_HOST_PASSWORD=your-email-app-password
OPENAI_API_KEY=your-openai-api-key
```

> The return URL is verified against Cashfree's Orders API before the local order is marked as paid. For production-grade reliability, add and verify a Cashfree webhook so payment updates do not depend only on the customer returning to the site.

## Run locally

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser.
