# System B - Integration Middleware

A middleware system that standardizes data from System A (currently ERPNext) for System C.

## Features

- Standardized data schemas using Pydantic models
- Adapter pattern for easy integration with different source systems
- RESTful API with versioning
- Comprehensive error handling
- Structured logging
- Retry mechanisms for flaky external systems
- Detailed API documentation with OpenAPI

## Architecture

The middleware follows a clean architecture approach:

- **Schemas**: Standardized data models using Pydantic
- **Adapters**: Connectors to external systems that transform data to/from standard format
- **API**: RESTful endpoints exposing standardized data
- **Core**: Core business logic and interfaces
- **Utils**: Utility functions for logging, error handling, etc.

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-org/system-b-middleware.git
   cd system-b-middleware
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   # Application settings
   DEBUG=False
   HOST=0.0.0.0
   PORT=8000
   LOG_LEVEL=INFO
   
   # Default adapter configuration
   DEFAULT_ADAPTER=erp_next
   # Entity-specific adapter overrides (optional)
   CUSTOMER_ADAPTER=cloud_erp
   PRODUCT_ADAPTER=erp_next
   QUOTATION_ADAPTER=erp_next
   INVOICE_ADAPTER=cloud_erp
   
   # System A (ERPNext) settings
   SYSTEM_A_BASE_URL=https://your-erp-instance.com
   SYSTEM_A_API_KEY=your_api_key
   SYSTEM_A_API_SECRET=your_api_secret
   
   # Retry settings
   MAX_RETRIES=3
   RETRY_BACKOFF_FACTOR=0.5
   ```

### Running the Application

Start the application:

```
python main.py
```

Or with uvicorn directly:

```
uvicorn main:app --reload
```

The API will be available at http://localhost:8000 and the API documentation at http://localhost:8000/docs.

## API Endpoints

The API follows RESTful conventions and includes the following endpoints:

### Customers

- `GET /api/v1/customers` - List customers
- `GET /api/v1/customers/{customer_id}` - Get a specific customer
- `POST /api/v1/customers` - Create a new customer
- `PUT /api/v1/customers/{customer_id}` - Update a customer
- `DELETE /api/v1/customers/{customer_id}` - Delete a customer

All endpoints accept an optional `adapter_name` query parameter to override the default adapter.

### Products

- `GET /api/v1/products` - List products
- `GET /api/v1/products/{product_id}` - Get a specific product
- `POST /api/v1/products` - Create a new product
- `PUT /api/v1/products/{product_id}` - Update a product
- `DELETE /api/v1/products/{product_id}` - Delete a product

### Quotations

- `GET /api/v1/quotations` - List quotations
- `GET /api/v1/quotations/{quotation_id}` - Get a specific quotation
- `POST /api/v1/quotations` - Create a new quotation
- `PUT /api/v1/quotations/{quotation_id}` - Update a quotation
- `DELETE /api/v1/quotations/{quotation_id}` - Delete a quotation

## Adding a New Adapter

To add support for a new system:

1. Create a new directory under `app/adapters/` for your system
2. Implement the adapter interface defined in `app/core/adapter.py`
3. Register your adapter in `app/core/adapter_factory.py`

## Running Tests

```
pytest
```

## License

[MIT](LICENSE) 