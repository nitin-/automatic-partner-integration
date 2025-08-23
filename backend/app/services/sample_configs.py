from typing import Dict, Any, List
from ..models.field_mapping import TransformationType, DataType
from ..models.integration import IntegrationType, AuthenticationType


class SampleConfigGenerator:
    """Service for generating sample lender configurations for testing"""
    
    @staticmethod
    def get_sample_lenders() -> List[Dict[str, Any]]:
        """Get sample lenders with different integration patterns"""
        return [
            {
                "name": "QuickLoan Pro",
                "description": "Fast personal loan provider with simple API",
                "contact_email": "api@quickloanpro.com",
                "contact_phone": "+1-800-QUICK-LOAN",
                "status": "active",
                "integration_pattern": "simple",
                "field_mappings": SampleConfigGenerator.get_quickloan_mappings(),
                "integration_sequence": SampleConfigGenerator.get_quickloan_sequence()
            },
            {
                "name": "SecureMortgage Bank",
                "description": "Traditional mortgage lender with complex validation",
                "contact_email": "integrations@securemortgage.com",
                "contact_phone": "+1-800-MORTGAGE",
                "status": "active",
                "integration_pattern": "complex",
                "field_mappings": SampleConfigGenerator.get_mortgage_mappings(),
                "integration_sequence": SampleConfigGenerator.get_mortgage_sequence()
            },
            {
                "name": "AutoFinance Express",
                "description": "Auto loan specialist with real-time approval",
                "contact_email": "dev@autofinance.com",
                "contact_phone": "+1-800-AUTO-LOAN",
                "status": "active",
                "integration_pattern": "real_time",
                "field_mappings": SampleConfigGenerator.get_auto_mappings(),
                "integration_sequence": SampleConfigGenerator.get_auto_sequence()
            },
            {
                "name": "BusinessCredit Plus",
                "description": "Business loan provider with document upload",
                "contact_email": "api@businesscredit.com",
                "contact_phone": "+1-800-BIZ-LOAN",
                "status": "active",
                "integration_pattern": "document_based",
                "field_mappings": SampleConfigGenerator.get_business_mappings(),
                "integration_sequence": SampleConfigGenerator.get_business_sequence()
            },
            {
                "name": "PaydayLend Now",
                "description": "Short-term loan provider with instant approval",
                "contact_email": "tech@paydaylend.com",
                "contact_phone": "+1-800-PAYDAY",
                "status": "active",
                "integration_pattern": "instant",
                "field_mappings": SampleConfigGenerator.get_payday_mappings(),
                "integration_sequence": SampleConfigGenerator.get_payday_sequence()
            }
        ]
    
    @staticmethod
    def get_quickloan_mappings() -> List[Dict[str, Any]]:
        """Simple personal loan field mappings"""
        return [
            {
                "name": "Customer Name",
                "source_field": "full_name",
                "target_field": "customer_name",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Email Address",
                "source_field": "email",
                "target_field": "email_address",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Phone Number",
                "source_field": "phone",
                "target_field": "mobile_number",
                "transformation_type": TransformationType.FORMAT_PHONE,
                "transformation_config": {"format": "clean"},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Loan Amount",
                "source_field": "loan_amount",
                "target_field": "requested_amount",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 2, "include_symbol": False},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Address",
                "source_field": "address",
                "target_field": "residential_address",
                "transformation_type": TransformationType.OBJECT_MAPPING,
                "transformation_config": {
                    "mapping": {
                        "street": "address_line_1",
                        "city": "city_name",
                        "state": "state_code",
                        "zip_code": "postal_code"
                    }
                },
                "is_required": True,
                "is_active": True
            }
        ]
    
    @staticmethod
    def get_mortgage_mappings() -> List[Dict[str, Any]]:
        """Complex mortgage field mappings"""
        return [
            {
                "name": "Customer Name",
                "source_field": "full_name",
                "target_field": "borrower_name",
                "transformation_type": TransformationType.SPLIT_NAME,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Email Address",
                "source_field": "email",
                "target_field": "contact_email",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Phone Number",
                "source_field": "phone",
                "target_field": "primary_phone",
                "transformation_type": TransformationType.FORMAT_PHONE,
                "transformation_config": {"format": "parentheses"},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Loan Amount",
                "source_field": "loan_amount",
                "target_field": "mortgage_amount",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 2, "include_symbol": True, "symbol": "$"},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Employment Status",
                "source_field": "employment_status",
                "target_field": "employment_type",
                "transformation_type": TransformationType.CONDITIONAL,
                "transformation_config": {
                    "conditions": {
                        "employed": "FULL_TIME",
                        "self_employed": "SELF_EMPLOYED",
                        "unemployed": "UNEMPLOYED",
                        "retired": "RETIRED"
                    }
                },
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Annual Income",
                "source_field": "annual_income",
                "target_field": "gross_annual_income",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 0, "include_symbol": False},
                "is_required": True,
                "is_active": True
            }
        ]
    
    @staticmethod
    def get_auto_mappings() -> List[Dict[str, Any]]:
        """Auto loan field mappings"""
        return [
            {
                "name": "Customer Name",
                "source_field": "full_name",
                "target_field": "applicant_name",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Vehicle Information",
                "source_field": "vehicle_info",
                "target_field": "vehicle_details",
                "transformation_type": TransformationType.OBJECT_MAPPING,
                "transformation_config": {
                    "mapping": {
                        "make": "vehicle_make",
                        "model": "vehicle_model",
                        "year": "vehicle_year",
                        "vin": "vin_number"
                    }
                },
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Loan Amount",
                "source_field": "loan_amount",
                "target_field": "financing_amount",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 2, "include_symbol": False},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Down Payment",
                "source_field": "down_payment",
                "target_field": "down_payment_amount",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 2, "include_symbol": False},
                "is_required": False,
                "is_active": True,
                "default_value": "0"
            }
        ]
    
    @staticmethod
    def get_business_mappings() -> List[Dict[str, Any]]:
        """Business loan field mappings"""
        return [
            {
                "name": "Business Name",
                "source_field": "business_name",
                "target_field": "company_name",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Business Owner",
                "source_field": "owner_name",
                "target_field": "primary_owner",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Business Type",
                "source_field": "business_type",
                "target_field": "entity_type",
                "transformation_type": TransformationType.CONDITIONAL,
                "transformation_config": {
                    "conditions": {
                        "llc": "LLC",
                        "corporation": "CORP",
                        "partnership": "PARTNERSHIP",
                        "sole_proprietorship": "SOLE_PROP"
                    }
                },
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Annual Revenue",
                "source_field": "annual_revenue",
                "target_field": "gross_revenue",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 0, "include_symbol": False},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Business Address",
                "source_field": "business_address",
                "target_field": "company_address",
                "transformation_type": TransformationType.OBJECT_MAPPING,
                "transformation_config": {
                    "mapping": {
                        "street": "address_line_1",
                        "city": "city",
                        "state": "state",
                        "zip_code": "zip"
                    }
                },
                "is_required": True,
                "is_active": True
            }
        ]
    
    @staticmethod
    def get_payday_mappings() -> List[Dict[str, Any]]:
        """Payday loan field mappings"""
        return [
            {
                "name": "Customer Name",
                "source_field": "full_name",
                "target_field": "customer_name",
                "transformation_type": TransformationType.NONE,
                "transformation_config": {},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Phone Number",
                "source_field": "phone",
                "target_field": "mobile_phone",
                "transformation_type": TransformationType.FORMAT_PHONE,
                "transformation_config": {"format": "clean"},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Loan Amount",
                "source_field": "loan_amount",
                "target_field": "advance_amount",
                "transformation_type": TransformationType.FORMAT_CURRENCY,
                "transformation_config": {"decimal_places": 2, "include_symbol": False},
                "is_required": True,
                "is_active": True
            },
            {
                "name": "Payday Date",
                "source_field": "next_payday",
                "target_field": "payday_date",
                "transformation_type": TransformationType.FORMAT_DATE,
                "transformation_config": {"input_format": "%Y-%m-%d", "output_format": "%m/%d/%Y"},
                "is_required": True,
                "is_active": True
            }
        ]
    
    @staticmethod
    def get_quickloan_sequence() -> Dict[str, Any]:
        """Simple single-step sequence"""
        return {
            "name": "QuickLoan Lead Submission",
            "description": "Simple lead submission to QuickLoan Pro",
            "sequence_type": "lead_submission",
            "execution_mode": "sequential",
            "stop_on_error": True,
            "retry_failed_steps": False,
            "is_active": True,
            "steps": [
                {
                    "name": "Submit Lead",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.quickloanpro.com/v1/leads",
                    "http_method": "POST",
                    "sequence_order": 1,
                    "auth_type": AuthenticationType.API_KEY,
                    "auth_config": {"header_name": "X-API-Key"},
                    "depends_on_fields": {},
                    "output_fields": ["lead_id", "status", "approval_code"]
                }
            ]
        }
    
    @staticmethod
    def get_mortgage_sequence() -> Dict[str, Any]:
        """Complex multi-step mortgage sequence"""
        return {
            "name": "SecureMortgage Application Process",
            "description": "Multi-step mortgage application with validation",
            "sequence_type": "lead_submission",
            "execution_mode": "sequential",
            "stop_on_error": True,
            "retry_failed_steps": True,
            "is_active": True,
            "steps": [
                {
                    "name": "Validate Application",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.securemortgage.com/v1/validate",
                    "http_method": "POST",
                    "sequence_order": 1,
                    "auth_type": AuthenticationType.BEARER_TOKEN,
                    "auth_config": {},
                    "depends_on_fields": {},
                    "output_fields": ["validation_id", "status", "errors"]
                },
                {
                    "name": "Submit Application",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.securemortgage.com/v1/applications",
                    "http_method": "POST",
                    "sequence_order": 2,
                    "auth_type": AuthenticationType.BEARER_TOKEN,
                    "auth_config": {},
                    "depends_on_fields": {"validation_id": "validation_id"},
                    "output_fields": ["application_id", "status", "loan_number"]
                },
                {
                    "name": "Request Documents",
                    "integration_type": IntegrationType.WEBHOOK,
                    "api_endpoint": "https://api.securemortgage.com/v1/documents/request",
                    "http_method": "POST",
                    "sequence_order": 3,
                    "auth_type": AuthenticationType.BEARER_TOKEN,
                    "auth_config": {},
                    "depends_on_fields": {"application_id": "application_id"},
                    "output_fields": ["document_request_id", "required_docs"]
                }
            ]
        }
    
    @staticmethod
    def get_auto_sequence() -> Dict[str, Any]:
        """Real-time auto loan sequence"""
        return {
            "name": "AutoFinance Express Approval",
            "description": "Real-time auto loan approval process",
            "sequence_type": "lead_submission",
            "execution_mode": "sequential",
            "stop_on_error": False,
            "retry_failed_steps": False,
            "is_active": True,
            "steps": [
                {
                    "name": "Credit Check",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.autofinance.com/v1/credit-check",
                    "http_method": "POST",
                    "sequence_order": 1,
                    "auth_type": AuthenticationType.API_KEY,
                    "auth_config": {"header_name": "X-API-Key"},
                    "depends_on_fields": {},
                    "output_fields": ["credit_score", "credit_status"]
                },
                {
                    "name": "Vehicle Valuation",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.autofinance.com/v1/vehicle-value",
                    "http_method": "POST",
                    "sequence_order": 2,
                    "auth_type": AuthenticationType.API_KEY,
                    "auth_config": {"header_name": "X-API-Key"},
                    "depends_on_fields": {},
                    "output_fields": ["vehicle_value", "loan_to_value"]
                },
                {
                    "name": "Instant Approval",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.autofinance.com/v1/approve",
                    "http_method": "POST",
                    "sequence_order": 3,
                    "auth_type": AuthenticationType.API_KEY,
                    "auth_config": {"header_name": "X-API-Key"},
                    "depends_on_fields": {
                        "credit_score": "credit_score",
                        "vehicle_value": "vehicle_value"
                    },
                    "output_fields": ["approval_status", "approved_amount", "interest_rate"]
                }
            ]
        }
    
    @staticmethod
    def get_business_sequence() -> Dict[str, Any]:
        """Document-based business loan sequence"""
        return {
            "name": "BusinessCredit Plus Application",
            "description": "Business loan with document upload",
            "sequence_type": "lead_submission",
            "execution_mode": "sequential",
            "stop_on_error": True,
            "retry_failed_steps": True,
            "is_active": True,
            "steps": [
                {
                    "name": "Submit Application",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.businesscredit.com/v1/applications",
                    "http_method": "POST",
                    "sequence_order": 1,
                    "auth_type": AuthenticationType.BASIC_AUTH,
                    "auth_config": {},
                    "depends_on_fields": {},
                    "output_fields": ["application_id", "status"]
                },
                {
                    "name": "Upload Documents",
                    "integration_type": IntegrationType.BULK_UPLOAD,
                    "api_endpoint": "https://api.businesscredit.com/v1/documents",
                    "http_method": "POST",
                    "sequence_order": 2,
                    "auth_type": AuthenticationType.BASIC_AUTH,
                    "auth_config": {},
                    "depends_on_fields": {"application_id": "application_id"},
                    "output_fields": ["document_ids", "upload_status"]
                },
                {
                    "name": "Underwriting Review",
                    "integration_type": IntegrationType.POLLING,
                    "api_endpoint": "https://api.businesscredit.com/v1/underwriting/status",
                    "http_method": "GET",
                    "sequence_order": 3,
                    "auth_type": AuthenticationType.BASIC_AUTH,
                    "auth_config": {},
                    "depends_on_fields": {"application_id": "application_id"},
                    "output_fields": ["underwriting_status", "decision", "loan_terms"]
                }
            ]
        }
    
    @staticmethod
    def get_payday_sequence() -> Dict[str, Any]:
        """Instant payday loan sequence"""
        return {
            "name": "PaydayLend Instant Approval",
            "description": "Instant payday loan approval",
            "sequence_type": "lead_submission",
            "execution_mode": "sequential",
            "stop_on_error": False,
            "retry_failed_steps": False,
            "is_active": True,
            "steps": [
                {
                    "name": "Instant Approval",
                    "integration_type": IntegrationType.LEAD_SUBMISSION,
                    "api_endpoint": "https://api.paydaylend.com/v1/instant-approval",
                    "http_method": "POST",
                    "sequence_order": 1,
                    "auth_type": AuthenticationType.API_KEY,
                    "auth_config": {"header_name": "X-API-Key"},
                    "depends_on_fields": {},
                    "output_fields": ["approval_status", "approved_amount", "funding_date"]
                }
            ]
        }
    
    @staticmethod
    def get_test_data_for_lender(lender_name: str) -> Dict[str, Any]:
        """Get appropriate test data for each lender type"""
        test_data_map = {
            "QuickLoan Pro": {
                "full_name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-123-4567",
                "loan_amount": "15000",
                "address": {
                    "street": "123 Main Street",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001"
                }
            },
            "SecureMortgage Bank": {
                "full_name": "Sarah Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "+1-555-987-6543",
                "loan_amount": "350000",
                "employment_status": "employed",
                "annual_income": "85000",
                "address": {
                    "street": "456 Oak Avenue",
                    "city": "Los Angeles",
                    "state": "CA",
                    "zip_code": "90210"
                }
            },
            "AutoFinance Express": {
                "full_name": "Mike Davis",
                "email": "mike.davis@email.com",
                "phone": "+1-555-456-7890",
                "loan_amount": "25000",
                "vehicle_info": {
                    "make": "Toyota",
                    "model": "Camry",
                    "year": "2022",
                    "vin": "1HGBH41JXMN109186"
                },
                "down_payment": "5000"
            },
            "BusinessCredit Plus": {
                "business_name": "TechStart Solutions",
                "owner_name": "Lisa Chen",
                "business_type": "llc",
                "annual_revenue": "500000",
                "business_address": {
                    "street": "789 Business Blvd",
                    "city": "Chicago",
                    "state": "IL",
                    "zip_code": "60601"
                }
            },
            "PaydayLend Now": {
                "full_name": "Robert Wilson",
                "email": "robert.wilson@email.com",
                "phone": "+1-555-321-6540",
                "loan_amount": "500",
                "next_payday": "2024-02-15"
            }
        }
        
        return test_data_map.get(lender_name, {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-000-0000",
            "loan_amount": "10000"
        })
