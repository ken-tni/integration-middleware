import sys
import logging
from app.core.conversions.quotation_converter import QuotationConverter
from app.utils.logging import setup_logging

# Setup logging
setup_logging(loglevel=logging.DEBUG)

def test_quotation_converter():
    # Create converter instance
    converter = QuotationConverter()
    
    # Test with minimal external data from ERP Next
    erp_next_data = {
        "name": "QTN-00001",
        "doctype": "Quotation"
        # No other fields provided to test default value handling
    }
    
    try:
        # Convert to standard format
        print("Converting from ERP Next format...")
        standard_quotation = converter.external_to_standard("erp_next", erp_next_data)
        print("Conversion successful!")
        print(f"Quotation ID: {standard_quotation.id}")
        print(f"Docstatus: {standard_quotation.docstatus}")
        print(f"Required fields filled: {all([
            standard_quotation.docstatus is not None,
            standard_quotation.order_type is not None,
            standard_quotation.company is not None,
            standard_quotation.conversion_rate is not None,
            standard_quotation.selling_price_list is not None,
            standard_quotation.price_list_currency is not None,
            standard_quotation.plc_conversion_rate is not None,
            standard_quotation.total_qty is not None,
            standard_quotation.base_total is not None,
            standard_quotation.base_net_total is not None,
            standard_quotation.net_total is not None,
            standard_quotation.base_grand_total is not None
        ])}")
        
        # Test conversion back to external format
        print("\nConverting back to ERP Next format...")
        external_data = converter.standard_to_external("erp_next", standard_quotation.dict())
        print("Conversion back successful!")
        print(f"External data: {external_data}")
        
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_quotation_converter()
    sys.exit(0 if success else 1) 