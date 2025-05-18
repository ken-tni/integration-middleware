from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import Field, BaseModel
from app.schemas.base import BaseSchema, MetadataSchema


class QuotationItem(BaseModel):
    """Quotation item schema."""
    item_code: str = Field(..., description="Item code")
    item_name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    qty: float = Field(..., description="Quantity")
    rate: float = Field(..., description="Rate")
    amount: float = Field(..., description="Amount")
    uom: str = Field(..., description="Unit of measure")


class Quotation(BaseSchema):
    """Standardized quotation schema."""
    name: str = Field(..., description="Quotation ID")
    owner: str = Field(..., description="Owner")
    creation: datetime = Field(..., description="Creation date")
    modified: datetime = Field(..., description="Modified date")
    modified_by: str = Field(..., description="Modified by")
    docstatus: int = Field(..., description="Document status")
    title: Optional[str] = Field(None, description="Title")
    naming_series: Optional[str] = Field(None, description="Naming series")
    quotation_to: str = Field(..., description="Quotation to")
    party_name: str = Field(..., description="Party name")
    customer_name: str = Field(..., description="Customer name")
    custom_quote_option2: Optional[str] = Field(None, description="Custom quote option 2")
    transaction_date: date = Field(..., description="Transaction date")
    valid_till: Optional[date] = Field(None, description="Valid till")
    order_type: str = Field(..., description="Order type")
    company: str = Field(..., description="Company")
    amended_from: Optional[str] = Field(None, description="Amended from")
    custom_customer_replied: Optional[bool] = Field(None, description="Customer replied")
    custom_quote_emailed: Optional[bool] = Field(None, description="Quote emailed")
    custom_quote_emailed_date: Optional[datetime] = Field(None, description="Quote emailed date")
    currency: str = Field(..., description="Currency")
    conversion_rate: float = Field(..., description="Conversion rate")
    selling_price_list: str = Field(..., description="Selling price list")
    price_list_currency: str = Field(..., description="Price list currency")
    plc_conversion_rate: float = Field(..., description="Price list conversion rate")
    ignore_pricing_rule: Optional[bool] = Field(None, description="Ignore pricing rule")
    scan_barcode: Optional[str] = Field(None, description="Scan barcode")
    custom_show_scope_of_works: Optional[bool] = Field(None, description="Show scope of works")
    custom_show_products: Optional[bool] = Field(None, description="Show products")
    custom_show_item: Optional[bool] = Field(None, description="Show item")
    custom_show_item_description: Optional[bool] = Field(None, description="Show item description")
    custom_show_qty: Optional[bool] = Field(None, description="Show quantity")
    custom_show_rate: Optional[bool] = Field(None, description="Show rate")
    custom_show_amount: Optional[bool] = Field(None, description="Show amount")
    tax_category: Optional[str] = Field(None, description="Tax category")
    taxes_and_charges: Optional[str] = Field(None, description="Taxes and charges")
    shipping_rule: Optional[str] = Field(None, description="Shipping rule")
    incoterm: Optional[str] = Field(None, description="Incoterm")
    named_place: Optional[str] = Field(None, description="Named place")
    total: float = Field(..., description="Total")
    custom_scope_of_work: Optional[str] = Field(None, description="Scope of work")
    custom_warranty: Optional[str] = Field(None, description="Warranty")
    total_qty: float = Field(..., description="Total quantity")
    total_net_weight: Optional[float] = Field(None, description="Total net weight")
    base_total: float = Field(..., description="Base total")
    base_net_total: float = Field(..., description="Base net total")
    net_total: float = Field(..., description="Net total")
    base_total_taxes_and_charges: Optional[float] = Field(None, description="Base total taxes and charges")
    base_grand_total: float = Field(..., description="Base grand total")
    base_rounding_adjustment: Optional[float] = Field(None, description="Base rounding adjustment")
    base_rounded_total: Optional[float] = Field(None, description="Base rounded total")
    base_in_words: Optional[str] = Field(None, description="Base in words")
    total_taxes_and_charges: Optional[float] = Field(None, description="Total taxes and charges")
    grand_total: float = Field(..., description="Grand total")
    rounding_adjustment: Optional[float] = Field(None, description="Rounding adjustment")
    rounded_total: Optional[float] = Field(None, description="Rounded total")
    disable_rounded_total: Optional[bool] = Field(None, description="Disable rounded total")
    additional_discount_percentage: Optional[float] = Field(None, description="Additional discount percentage")
    discount_amount: Optional[float] = Field(None, description="Discount amount")
    apply_discount_on: Optional[str] = Field(None, description="Apply discount on")
    in_words: Optional[str] = Field(None, description="In words")
    base_discount_amount: Optional[float] = Field(None, description="Base discount amount")
    coupon_code: Optional[str] = Field(None, description="Coupon code")
    referral_sales_partner: Optional[str] = Field(None, description="Referral sales partner")
    other_charges_calculation: Optional[str] = Field(None, description="Other charges calculation")
    customer_address: Optional[str] = Field(None, description="Customer address")
    address_display: Optional[str] = Field(None, description="Address display")
    contact_person: Optional[str] = Field(None, description="Contact person")
    contact_display: Optional[str] = Field(None, description="Contact display")
    contact_mobile: Optional[str] = Field(None, description="Contact mobile")
    contact_email: Optional[str] = Field(None, description="Contact email")
    shipping_address_name: Optional[str] = Field(None, description="Shipping address name")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    company_address: Optional[str] = Field(None, description="Company address")
    company_contact_person: Optional[str] = Field(None, description="Company contact person")
    company_address_display: Optional[str] = Field(None, description="Company address display")
    payment_terms_template: Optional[str] = Field(None, description="Payment terms template")
    tc_name: Optional[str] = Field(None, description="Terms and conditions name")
    auto_repeat: Optional[str] = Field(None, description="Auto repeat")
    letter_head: Optional[str] = Field(None, description="Letter head")
    group_same_items: Optional[bool] = Field(None, description="Group same items")
    select_print_heading: Optional[str] = Field(None, description="Select print heading")
    language: Optional[str] = Field(None, description="Language")
    order_lost_reason: Optional[str] = Field(None, description="Order lost reason")
    status: str = Field(..., description="Status")
    customer_group: Optional[str] = Field(None, description="Customer group")
    territory: Optional[str] = Field(None, description="Territory")
    campaign: Optional[str] = Field(None, description="Campaign")
    source: Optional[str] = Field(None, description="Source")
    opportunity: Optional[str] = Field(None, description="Opportunity")
    supplier_quotation: Optional[str] = Field(None, description="Supplier quotation")
    items: List[QuotationItem] = Field(default_factory=list, description="Quotation items")
    metadata: MetadataSchema = Field(..., description="Source system metadata")


class QuotationResponse(BaseSchema):
    """Quotation response schema for API endpoints."""
    name: str
    title: Optional[str] = None
    customer_name: str
    transaction_date: date
    valid_till: Optional[date] = None
    currency: str
    status: str
    total: float
    grand_total: float
    items: List[QuotationItem]


class QuotationList(BaseModel):
    """List of quotations response schema."""
    total: int = Field(..., description="Total number of quotations")
    quotations: List[QuotationResponse] = Field(..., description="List of quotations") 