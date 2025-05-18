from datetime import datetime, date
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from app.adapters.erp_next.client import ERPNextClient
from app.core.adapter import BaseAdapter
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.schemas.customer import Customer
from app.schemas.product import Product
from app.schemas.quotation import Quotation, QuotationItem
from app.schemas.base import MetadataSchema
from app.utils.logging import get_logger

T = TypeVar('T', Customer, Product, Quotation)
logger = get_logger("erp_next_adapter")


class ERPNextAdapter(BaseAdapter[T]):
    """Adapter for ERPNext API."""
    
    def __init__(self, client: Optional[ERPNextClient] = None):
        """Initialize the ERPNext adapter.
        
        Args:
            client: Optional ERPNext client instance
        """
        self.client = client or ERPNextClient()
        self._entity_type_map = {
            "customer": "Customer",
            "product": "Item",
            "quotation": "Quotation",
        }
    
    async def connect(self) -> None:
        """Initialize connection to ERPNext."""
        # Nothing to do here as the client is already initialized
        logger.debug("ERPNext adapter connected")
    
    async def get_by_id(self, entity_type: str, entity_id: str) -> T:
        """Get a single entity by ID from ERPNext.
        
        Args:
            entity_type: The type of entity to retrieve (e.g., "customer", "product")
            entity_id: The ID of the entity in ERPNext
            
        Returns:
            The standardized entity object
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Get data from ERPNext
            path = f"/api/resource/{erp_entity_type}/{entity_id}"
            # Request all fields
            params = {
                "fields": '["*"]'  # Request all fields
            }
            response = await self.client.get(path, params=params)
            
            # Debug log the raw response
            logger.debug(f"Raw {entity_type} data from ERPNext: {response}")
            
            # Convert to standardized format
            if entity_type == "customer":
                return self._convert_customer(response.get("data", {}))
            elif entity_type == "product":
                return self._convert_product(response.get("data", {}))
            elif entity_type == "quotation":
                return self._convert_quotation(response.get("data", {}))
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to get {entity_type} with ID {entity_id}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def search(
        self, entity_type: str, filters: Dict[str, Any], page: int = 1, page_size: int = 100
    ) -> Dict[str, Any]:
        """Search for entities in ERPNext.
        
        Args:
            entity_type: The type of entity to search for
            filters: Dict of filter parameters
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict containing total count and list of entities
            
        Raises:
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Calculate pagination parameters
            limit_start = (page - 1) * page_size
            limit_page_length = page_size
            
            # Convert filters to ERPNext format
            erp_filters = self._convert_filters_to_erp(entity_type, filters)
            
            # Get data from ERPNext
            path = f"/api/resource/{erp_entity_type}"
            params = {
                "filters": erp_filters,
                "limit_start": limit_start,
                "limit_page_length": limit_page_length,
                "fields": '["*"]'  # Request all fields
            }
            response = await self.client.get(path, params=params)
            
            # Debug log the raw response
            logger.debug(f"Raw {entity_type} search results from ERPNext: {response}")
            
            # # Get total count
            # count_response = await self.client.get(
            #     f"/api/resource/{erp_entity_type}/count",
            #     params={"filters": erp_filters},
            # )
            # total = count_response.get("count", 0)
            total = 0
            # Convert to standardized format
            items = response.get("data", [])
            if entity_type == "customer":
                customers = [self._convert_customer(item) for item in items]
                return {"total": total, "customers": customers}
            elif entity_type == "product":
                products = [self._convert_product(item) for item in items]
                return {"total": total, "products": products}
            elif entity_type == "quotation":
                quotations = [self._convert_quotation(item) for item in items]
                return {"total": total, "quotations": quotations}
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
        
        except Exception as e:
            logger.error(f"Error searching for {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to search for {entity_type}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> T:
        """Create a new entity in ERPNext.
        
        Args:
            entity_type: The type of entity to create
            data: The data for the new entity
            
        Returns:
            The created entity in standardized format
            
        Raises:
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Convert to ERPNext format
            if entity_type == "customer":
                erp_data = self._convert_customer_to_erp(data)
            elif entity_type == "product":
                erp_data = self._convert_product_to_erp(data)
            elif entity_type == "quotation":
                erp_data = self._convert_quotation_to_erp(data)
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
            
            # Create in ERPNext
            path = f"/api/resource/{erp_entity_type}"
            response = await self.client.post(path, data=erp_data)
            
            # Get the created entity
            created_id = response.get("data", {}).get("name")
            if not created_id:
                raise AdapterError(
                    message=f"Failed to get ID of created {entity_type}",
                    source_system="ERPNext",
                )
            
            return await self.get_by_id(entity_type, created_id)
        
        except Exception as e:
            logger.error(f"Error creating {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to create {entity_type}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> T:
        """Update an existing entity in ERPNext.
        
        Args:
            entity_type: The type of entity to update
            entity_id: The ID of the entity to update
            data: The fields to update
            
        Returns:
            The updated entity in standardized format
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Convert to ERPNext format
            if entity_type == "customer":
                erp_data = self._convert_customer_to_erp(data)
            elif entity_type == "product":
                erp_data = self._convert_product_to_erp(data)
            elif entity_type == "quotation":
                erp_data = self._convert_quotation_to_erp(data)
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
            
            # Update in ERPNext
            path = f"/api/resource/{erp_entity_type}/{entity_id}"
            await self.client.put(path, data=erp_data)
            
            # Get the updated entity
            return await self.get_by_id(entity_type, entity_id)
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to update {entity_type} with ID {entity_id}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity in ERPNext.
        
        Args:
            entity_type: The type of entity to delete
            entity_id: The ID of the entity to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Delete in ERPNext
            path = f"/api/resource/{erp_entity_type}/{entity_id}"
            await self.client.delete(path)
            return True
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to delete {entity_type} with ID {entity_id}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def close(self):
        """Close the adapter and its client."""
        if self.client:
            await self.client.close()
    
    def _get_erp_entity_type(self, entity_type: str) -> str:
        """Convert standard entity type to ERPNext entity type."""
        erp_type = self._entity_type_map.get(entity_type.lower())
        if not erp_type:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        return erp_type
    
    def _convert_filters_to_erp(self, entity_type: str, filters: Dict[str, Any]) -> List[List[str]]:
        """Convert standard filters to ERPNext filter format."""
        # ERPNext uses a specific filter format: [[field, operator, value], ...]
        erp_filters = []
        
        # Map standard fields to ERPNext fields
        field_map = {
            "customer": {
                "name": "customer_name",
                "email": "email_id",
                "status": "status",
            },
            "product": {
                "name": "item_name",
                "sku": "item_code",
                "category": "item_group",
                "is_active": "disabled",  # Note: this is inverted in ERPNext
            },
            "quotation": {
                "customer_name": "customer_name",
                "status": "status",
                "transaction_date_gte": "transaction_date",
                "transaction_date_lte": "transaction_date",
                "transaction_date_range": "transaction_date",
            }
        }
        
        # Get the field map for this entity type
        entity_field_map = field_map.get(entity_type, {})
        
        for field, value in filters.items():
            # Map the field name if needed
            erp_field = entity_field_map.get(field, field)
            
            # Handle special cases
            if field == "is_active" and entity_type == "product":
                # ERPNext uses "disabled" which is the inverse of "is_active"
                erp_filters.append([erp_field, "=", not value])
            elif field == "transaction_date_gte":
                erp_filters.append([erp_field, ">=", value])
            elif field == "transaction_date_lte":
                erp_filters.append([erp_field, "<=", value])
            elif field == "transaction_date_range" and isinstance(value, tuple) and len(value) == 2:
                from_date, to_date = value
                erp_filters.append([erp_field, "between", [from_date, to_date]])
            else:
                # Standard case
                erp_filters.append([erp_field, "=", value])
        
        return erp_filters
    
    def _convert_customer(self, erp_customer: Dict[str, Any]) -> Customer:
        """Convert ERPNext customer to standardized format."""
        # Log all available fields in the ERPNext customer data
        logger.debug(f"Available fields in ERPNext customer: {list(erp_customer.keys())}")
        
        # Log specific fields we're interested in
        fields_to_check = ["name", "customer_name", "customer_type", "email_id", "mobile_no", 
                          "website", "customer_group", "territory", "gender", "language"]
        for field in fields_to_check:
            logger.debug(f"Field '{field}' value: {erp_customer.get(field)}")
        
        # Extract address if available
        address = {}
        if erp_customer.get("address_line1"):
            address = {
                "street1": erp_customer.get("address_line1", ""),
                "street2": erp_customer.get("address_line2", ""),
                "city": erp_customer.get("city", ""),
                "state": erp_customer.get("state", ""),
                "postal_code": erp_customer.get("pincode", ""),
                "country": erp_customer.get("country", ""),
            }
        
        # Create standardized customer
        return Customer(
            id=erp_customer.get("name", ""),
            name=erp_customer.get("customer_name", ""),
            customer_type=erp_customer.get("customer_type", "Company"),
            contact_info={
                "email": erp_customer.get("email_id"),
                "phone": erp_customer.get("phone"),
                "mobile": erp_customer.get("mobile_no"),
                "website": erp_customer.get("website"),
                "address": address if address.get("street1") else None,
            },
            tax_id=erp_customer.get("tax_id"),
            status=erp_customer.get("status", "Active"),
            credit_limit=float(erp_customer.get("credit_limit", 0)) if erp_customer.get("credit_limit") else None,
            notes=erp_customer.get("notes"),
            created_at=self._parse_date(erp_customer.get("creation")),
            updated_at=self._parse_date(erp_customer.get("modified")),
            # Additional ERPNext fields
            owner=erp_customer.get("owner"),
            modified_by=erp_customer.get("modified_by"),
            docstatus=erp_customer.get("docstatus"),
            naming_series=erp_customer.get("naming_series"),
            salutation=erp_customer.get("salutation"),
            customer_group=erp_customer.get("customer_group"),
            territory=erp_customer.get("territory"),
            gender=erp_customer.get("gender"),
            lead_name=erp_customer.get("lead_name"),
            opportunity_name=erp_customer.get("opportunity_name"),
            prospect_name=erp_customer.get("prospect_name"),
            account_manager=erp_customer.get("account_manager"),
            image=erp_customer.get("image"),
            language=erp_customer.get("language"),
            market_segment=erp_customer.get("market_segment"),
            default_currency=erp_customer.get("default_currency"),
            metadata=MetadataSchema(
                source_system="ERPNext",
                source_id=erp_customer.get("name", ""),
                raw_data=erp_customer,
            ),
        )
    
    def _convert_product(self, erp_product: Dict[str, Any]) -> Product:
        """Convert ERPNext product to standardized format."""
        # Extract attributes if available
        attributes = []
        for attr in erp_product.get("attributes", []):
            attributes.append({
                "name": attr.get("attribute"),
                "value": attr.get("attribute_value"),
            })
        
        # Create standardized product
        return Product(
            id=erp_product.get("name", ""),
            name=erp_product.get("item_name", ""),
            sku=erp_product.get("item_code", ""),
            description=erp_product.get("description", ""),
            category=erp_product.get("item_group", ""),
            price=float(erp_product.get("standard_rate", 0)),
            cost=float(erp_product.get("valuation_rate", 0)) if erp_product.get("valuation_rate") else None,
            tax_rate=float(erp_product.get("tax_rate", 0)) if erp_product.get("tax_rate") else None,
            stock_quantity=int(erp_product.get("actual_qty", 0)),
            unit_of_measure=erp_product.get("stock_uom", ""),
            attributes=attributes,
            is_active=not erp_product.get("disabled", False),  # Note: this is inverted in ERPNext
            created_at=self._parse_date(erp_product.get("creation")),
            updated_at=self._parse_date(erp_product.get("modified")),
            metadata=MetadataSchema(
                source_system="ERPNext",
                source_id=erp_product.get("name", ""),
                raw_data=erp_product,
            ),
        )
    
    def _convert_customer_to_erp(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standardized customer data to ERPNext format."""
        erp_data = {
            "doctype": "Customer",
            "customer_name": customer_data.get("name", ""),
            "customer_type": customer_data.get("customer_type", "Company"),
            # Use direct fields if available, otherwise fall back to contact_info
            "email_id": customer_data.get("email_id") or customer_data.get("contact_info", {}).get("email"),
            "phone": customer_data.get("contact_info", {}).get("phone"),
            "mobile_no": customer_data.get("mobile_no") or customer_data.get("contact_info", {}).get("mobile"),
            "website": customer_data.get("website") or customer_data.get("contact_info", {}).get("website"),
            "tax_id": customer_data.get("tax_id"),
            "status": customer_data.get("status", "Active"),
            "credit_limit": customer_data.get("credit_limit"),
            "notes": customer_data.get("notes"),
            # Additional ERPNext fields
            "owner": customer_data.get("owner"),
            "modified_by": customer_data.get("modified_by"),
            "docstatus": customer_data.get("docstatus"),
            "naming_series": customer_data.get("naming_series"),
            "salutation": customer_data.get("salutation"),
            "customer_group": customer_data.get("customer_group"),
            "territory": customer_data.get("territory"),
            "gender": customer_data.get("gender"),
            "lead_name": customer_data.get("lead_name"),
            "opportunity_name": customer_data.get("opportunity_name"),
            "prospect_name": customer_data.get("prospect_name"),
            "account_manager": customer_data.get("account_manager"),
            "image": customer_data.get("image"),
            "language": customer_data.get("language"),
            "market_segment": customer_data.get("market_segment"),
            "default_currency": customer_data.get("default_currency"),
        }
        
        # Add address fields if available
        address = customer_data.get("contact_info", {}).get("address", {})
        if address:
            erp_data.update({
                "address_line1": address.get("street1", ""),
                "address_line2": address.get("street2", ""),
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "pincode": address.get("postal_code", ""),
                "country": address.get("country", ""),
            })
        
        # Remove None values
        return {k: v for k, v in erp_data.items() if v is not None}
    
    def _convert_product_to_erp(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standardized product data to ERPNext format."""
        erp_data = {
            "doctype": "Item",
            "item_name": product_data.get("name", ""),
            "item_code": product_data.get("sku", ""),
            "description": product_data.get("description", ""),
            "item_group": product_data.get("category", ""),
            "standard_rate": product_data.get("price", 0),
            "valuation_rate": product_data.get("cost"),
            "tax_rate": product_data.get("tax_rate"),
            "stock_uom": product_data.get("unit_of_measure", ""),
            "disabled": not product_data.get("is_active", True),  # Note: this is inverted in ERPNext
        }
        
        # Add attributes if available
        attributes = product_data.get("attributes", [])
        if attributes:
            erp_data["attributes"] = [
                {
                    "attribute": attr.get("name", ""),
                    "attribute_value": attr.get("value", ""),
                }
                for attr in attributes
            ]
        
        return erp_data
    
    def _convert_quotation(self, erp_quotation: Dict[str, Any]) -> Quotation:
        """Convert ERPNext quotation to standardized format."""
        # Extract items if available
        items = []
        for item in erp_quotation.get("items", []):
            items.append(QuotationItem(
                item_code=item.get("item_code", ""),
                item_name=item.get("item_name", ""),
                description=item.get("description", ""),
                qty=float(item.get("qty", 0)),
                rate=float(item.get("rate", 0)),
                amount=float(item.get("amount", 0)),
                uom=item.get("uom", ""),
            ))
        
        # Parse dates
        transaction_date = self._parse_date_str(erp_quotation.get("transaction_date"))
        valid_till = self._parse_date_str(erp_quotation.get("valid_till"))
        
        # Create standardized quotation
        return Quotation(
            id=erp_quotation.get("name", ""),
            name=erp_quotation.get("name", ""),
            owner=erp_quotation.get("owner", ""),
            creation=self._parse_date(erp_quotation.get("creation")),
            modified=self._parse_date(erp_quotation.get("modified")),
            modified_by=erp_quotation.get("modified_by", ""),
            docstatus=erp_quotation.get("docstatus", 0),
            title=erp_quotation.get("title"),
            naming_series=erp_quotation.get("naming_series"),
            quotation_to=erp_quotation.get("quotation_to", ""),
            party_name=erp_quotation.get("party_name", ""),
            customer_name=erp_quotation.get("customer_name", ""),
            custom_quote_option2=erp_quotation.get("custom_quote_option2"),
            transaction_date=transaction_date if transaction_date else date.today(),  # Provide default value
            valid_till=valid_till,
            order_type=erp_quotation.get("order_type", ""),
            company=erp_quotation.get("company", ""),
            amended_from=erp_quotation.get("amended_from"),
            custom_customer_replied=erp_quotation.get("custom_customer_replied"),
            custom_quote_emailed=erp_quotation.get("custom_quote_emailed"),
            custom_quote_emailed_date=self._parse_date(erp_quotation.get("custom_quote_emailed_date")),
            currency=erp_quotation.get("currency", ""),
            conversion_rate=float(erp_quotation.get("conversion_rate", 1.0)),
            selling_price_list=erp_quotation.get("selling_price_list", ""),
            price_list_currency=erp_quotation.get("price_list_currency", ""),
            plc_conversion_rate=float(erp_quotation.get("plc_conversion_rate", 1.0)),
            ignore_pricing_rule=erp_quotation.get("ignore_pricing_rule"),
            scan_barcode=erp_quotation.get("scan_barcode"),
            custom_show_scope_of_works=erp_quotation.get("custom_show_scope_of_works"),
            custom_show_products=erp_quotation.get("custom_show_products"),
            custom_show_item=erp_quotation.get("custom_show_item"),
            custom_show_item_description=erp_quotation.get("custom_show_item_description"),
            custom_show_qty=erp_quotation.get("custom_show_qty"),
            custom_show_rate=erp_quotation.get("custom_show_rate"),
            custom_show_amount=erp_quotation.get("custom_show_amount"),
            tax_category=erp_quotation.get("tax_category"),
            taxes_and_charges=erp_quotation.get("taxes_and_charges"),
            shipping_rule=erp_quotation.get("shipping_rule"),
            incoterm=erp_quotation.get("incoterm"),
            named_place=erp_quotation.get("named_place"),
            total=float(erp_quotation.get("total", 0)),
            custom_scope_of_work=erp_quotation.get("custom_scope_of_work"),
            custom_warranty=erp_quotation.get("custom_warranty"),
            total_qty=float(erp_quotation.get("total_qty", 0)),
            total_net_weight=float(erp_quotation.get("total_net_weight", 0)) if erp_quotation.get("total_net_weight") else None,
            base_total=float(erp_quotation.get("base_total", 0)),
            base_net_total=float(erp_quotation.get("base_net_total", 0)),
            net_total=float(erp_quotation.get("net_total", 0)),
            base_total_taxes_and_charges=float(erp_quotation.get("base_total_taxes_and_charges", 0)) if erp_quotation.get("base_total_taxes_and_charges") else None,
            base_grand_total=float(erp_quotation.get("base_grand_total", 0)),
            base_rounding_adjustment=float(erp_quotation.get("base_rounding_adjustment", 0)) if erp_quotation.get("base_rounding_adjustment") else None,
            base_rounded_total=float(erp_quotation.get("base_rounded_total", 0)) if erp_quotation.get("base_rounded_total") else None,
            base_in_words=erp_quotation.get("base_in_words"),
            total_taxes_and_charges=float(erp_quotation.get("total_taxes_and_charges", 0)) if erp_quotation.get("total_taxes_and_charges") else None,
            grand_total=float(erp_quotation.get("grand_total", 0)),
            rounding_adjustment=float(erp_quotation.get("rounding_adjustment", 0)) if erp_quotation.get("rounding_adjustment") else None,
            rounded_total=float(erp_quotation.get("rounded_total", 0)) if erp_quotation.get("rounded_total") else None,
            disable_rounded_total=erp_quotation.get("disable_rounded_total"),
            additional_discount_percentage=float(erp_quotation.get("additional_discount_percentage", 0)) if erp_quotation.get("additional_discount_percentage") else None,
            discount_amount=float(erp_quotation.get("discount_amount", 0)) if erp_quotation.get("discount_amount") else None,
            apply_discount_on=erp_quotation.get("apply_discount_on"),
            in_words=erp_quotation.get("in_words"),
            base_discount_amount=float(erp_quotation.get("base_discount_amount", 0)) if erp_quotation.get("base_discount_amount") else None,
            coupon_code=erp_quotation.get("coupon_code"),
            referral_sales_partner=erp_quotation.get("referral_sales_partner"),
            other_charges_calculation=erp_quotation.get("other_charges_calculation"),
            customer_address=erp_quotation.get("customer_address"),
            address_display=erp_quotation.get("address_display"),
            contact_person=erp_quotation.get("contact_person"),
            contact_display=erp_quotation.get("contact_display"),
            contact_mobile=erp_quotation.get("contact_mobile"),
            contact_email=erp_quotation.get("contact_email"),
            shipping_address_name=erp_quotation.get("shipping_address_name"),
            shipping_address=erp_quotation.get("shipping_address"),
            company_address=erp_quotation.get("company_address"),
            company_contact_person=erp_quotation.get("company_contact_person"),
            company_address_display=erp_quotation.get("company_address_display"),
            payment_terms_template=erp_quotation.get("payment_terms_template"),
            tc_name=erp_quotation.get("tc_name"),
            auto_repeat=erp_quotation.get("auto_repeat"),
            letter_head=erp_quotation.get("letter_head"),
            group_same_items=erp_quotation.get("group_same_items"),
            select_print_heading=erp_quotation.get("select_print_heading"),
            language=erp_quotation.get("language"),
            order_lost_reason=erp_quotation.get("order_lost_reason"),
            status=erp_quotation.get("status", ""),
            customer_group=erp_quotation.get("customer_group"),
            territory=erp_quotation.get("territory"),
            campaign=erp_quotation.get("campaign"),
            source=erp_quotation.get("source"),
            opportunity=erp_quotation.get("opportunity"),
            supplier_quotation=erp_quotation.get("supplier_quotation"),
            items=items,
            # Add required BaseSchema fields
            created_at=self._parse_date(erp_quotation.get("creation")),
            updated_at=self._parse_date(erp_quotation.get("modified")),
            metadata=MetadataSchema(
                source_system="ERPNext",
                source_id=erp_quotation.get("name", ""),
                raw_data=erp_quotation,
            ),
        )
    
    def _convert_quotation_to_erp(self, quotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standardized quotation data to ERPNext format."""
        # Convert items
        items = []
        for item in quotation_data.get("items", []):
            items.append({
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name"),
                "description": item.get("description"),
                "qty": item.get("qty"),
                "rate": item.get("rate"),
                "uom": item.get("uom"),
            })
        
        # Convert dates to strings
        transaction_date = quotation_data.get("transaction_date")
        if transaction_date and not isinstance(transaction_date, str):
            transaction_date = transaction_date.isoformat()
        
        valid_till = quotation_data.get("valid_till")
        if valid_till and not isinstance(valid_till, str):
            valid_till = valid_till.isoformat()
        
        # Create ERPNext quotation data
        erp_data = {
            "doctype": "Quotation",
            "title": quotation_data.get("title"),
            "naming_series": quotation_data.get("naming_series"),
            "quotation_to": quotation_data.get("quotation_to"),
            "party_name": quotation_data.get("party_name"),
            "customer_name": quotation_data.get("customer_name"),
            "transaction_date": transaction_date,
            "valid_till": valid_till,
            "order_type": quotation_data.get("order_type"),
            "company": quotation_data.get("company"),
            "currency": quotation_data.get("currency"),
            "conversion_rate": quotation_data.get("conversion_rate"),
            "selling_price_list": quotation_data.get("selling_price_list"),
            "price_list_currency": quotation_data.get("price_list_currency"),
            "plc_conversion_rate": quotation_data.get("plc_conversion_rate"),
            "ignore_pricing_rule": quotation_data.get("ignore_pricing_rule"),
            "tax_category": quotation_data.get("tax_category"),
            "taxes_and_charges": quotation_data.get("taxes_and_charges"),
            "shipping_rule": quotation_data.get("shipping_rule"),
            "custom_scope_of_work": quotation_data.get("custom_scope_of_work"),
            "custom_warranty": quotation_data.get("custom_warranty"),
            "apply_discount_on": quotation_data.get("apply_discount_on"),
            "additional_discount_percentage": quotation_data.get("additional_discount_percentage"),
            "discount_amount": quotation_data.get("discount_amount"),
            "customer_address": quotation_data.get("customer_address"),
            "contact_person": quotation_data.get("contact_person"),
            "shipping_address_name": quotation_data.get("shipping_address_name"),
            "company_address": quotation_data.get("company_address"),
            "payment_terms_template": quotation_data.get("payment_terms_template"),
            "tc_name": quotation_data.get("tc_name"),
            "letter_head": quotation_data.get("letter_head"),
            "language": quotation_data.get("language"),
            "customer_group": quotation_data.get("customer_group"),
            "territory": quotation_data.get("territory"),
            "campaign": quotation_data.get("campaign"),
            "source": quotation_data.get("source"),
            "opportunity": quotation_data.get("opportunity"),
            "items": items,
        }
        
        # Remove None values
        return {k: v for k, v in erp_data.items() if v is not None}
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse date string from ERPNext."""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            # Fallback to current time if parsing fails
            return datetime.now()
    
    def _parse_date_str(self, date_str: Optional[str]) -> Optional[datetime.date]:
        """Parse date string from ERPNext."""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            return None 