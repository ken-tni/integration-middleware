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

## After adding new Adapter
if the new adapter is implemented correctly, the external API of the middleware (e.g., GET /api/v1/customers and the field names like name, email it returns) should NOT change.
Here's why:
Standardized Schemas (app/schemas/): This middleware uses Pydantic models in app/schemas/ to define a standardized structure for data. For example, there's likely a CustomerSchema that dictates that a customer object will always have fields like id, customer_name, contact_email, etc. (the exact names would be in those schema files).
Adapter's Responsibility: When you create a new adapter for your new ERP system (let's call it "NewERP"):
Your NewERP adapter will fetch data from NewERP. This data will have field names specific to NewERP (e.g., NewERP might use cust_id, officialName, emailAddr).
The crucial job of your NewERP adapter (in app/adapters/new_erp/) is to transform this data from NewERP's format into the middleware's standardized schema format. So, it would map cust_id to id, officialName to customer_name, emailAddr to contact_email, and so on.
Consistent API Output: The API endpoints defined in app/api/v1/endpoints/ are designed to always return data that conforms to these standardized Pydantic schemas. They rely on the currently active adapter (whether it's ERPNext or your NewERP adapter) to provide data in that standard format.
Therefore, the whole point of this middleware architecture is to decouple System C (and other API consumers) from the specifics of System A (the ERP).
System C interacts with the middleware's consistent API.
The middleware, via its adapter layer, handles the translation to/from whatever ERP system is plugged in at the back.
So, if you switch from ERPNext to NewERP:
You will write a new adapter for NewERP.
This adapter will ensure that data from NewERP is mapped to the existing, standardized Pydantic schemas.
The API endpoints will continue to serve data in that same standardized format.
Systems consuming the middleware's API will continue to receive data with the same field names and structure as before, and they will not need to be changed.
This is the power of using an adapter pattern and standardized schemas in an integration middleware. It isolates changes in one system from affecting others.

## How Add new Adapter 
Create a New Adapter Directory:
You'll need to create a new folder for your target system within the app/adapters/ directory. For example, if your new system is called "AwesomeERP", you would create app/adapters/awesome_erp/.
Implement the Adapter Interface:
The system has a defined "adapter interface" located in app/core/adapter.py. This interface will specify the methods that any adapter (like the current ERPNext one, or your new one) must implement.
Inside your new adapter directory (e.g., app/adapters/awesome_erp/), you'll create Python files that contain a class (or classes) implementing all the methods defined in app/core/adapter.py.
These methods will handle the communication with your "AwesomeERP" system and will be responsible for:
Fetching data (e.g., customers, products, quotations).
Transforming that data from "AwesomeERP"'s format into the standardized Pydantic schemas defined in app/schemas/.
Potentially, sending data from the standardized schemas back to "AwesomeERP" (for POST, PUT, DELETE operations).
Register Your New Adapter:
There's a file, app/core/adapter_factory.py, which is likely responsible for creating instances of the correct adapter when needed.
You'll need to modify this file to make the system aware of your new "AwesomeERP" adapter. This might involve adding it to a dictionary or a conditional logic block that chooses the adapter based on configuration or some other criteria.
In essence:
The current ERPNext adapter in app/adapters/erp_next/ serves as a template. You'd replicate its structure and purpose but tailor the internal logic to interact with your new system's API or data access methods. The goal is always to convert data to and from the common Pydantic models used throughout the middleware.
To give you more specific details on what you'd need to implement, I can show you the contents of:
app/core/adapter.py (to see the interface you need to implement)
app/core/adapter_factory.py (to see how adapters are registered and chosen)

```
pytest
```

## License

[MIT](LICENSE) 
