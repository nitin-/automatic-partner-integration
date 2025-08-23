import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from ..models.field_mapping import FieldMapping, TransformationType, DataType
import structlog

logger = structlog.get_logger()


class DataTransformer:
    """Engine for transforming data based on field mappings"""
    
    def __init__(self):
        self.transformers = {
            TransformationType.NONE: self._no_transform,
            TransformationType.FORMAT_PHONE: self._format_phone,
            TransformationType.FORMAT_DATE: self._format_date,
            TransformationType.FORMAT_CURRENCY: self._format_currency,
            TransformationType.SPLIT_NAME: self._split_name,
            TransformationType.OBJECT_MAPPING: self._object_mapping,
            TransformationType.ARRAY_FORMAT: self._array_format,
            TransformationType.CONDITIONAL: self._conditional_transform,
            TransformationType.CUSTOM: self._custom_transform,
        }
    
    def transform_data(
        self, 
        source_data: Dict[str, Any], 
        field_mappings: List[FieldMapping]
    ) -> Dict[str, Any]:
        """Transform source data according to field mappings"""
        try:
            transformed_data = {}
            
            for mapping in field_mappings:
                if not mapping.is_active:
                    continue
                
                # Extract source value
                source_value = self._extract_value(source_data, mapping.source_field, mapping.source_field_path)
                
                # Apply transformation
                transformed_value = self._apply_transformation(
                    source_value, 
                    mapping.transformation_type, 
                    mapping.transformation_config
                )
                
                # Validate transformed value
                if not self._validate_value(transformed_value, mapping):
                    if mapping.fallback_value is not None:
                        transformed_value = mapping.fallback_value
                    elif mapping.is_required:
                        logger.warning(
                            "Required field validation failed",
                            field=mapping.source_field,
                            value=transformed_value
                        )
                        continue
                
                # Set target value
                self._set_value(transformed_data, mapping.target_field, mapping.target_field_path, transformed_value)
            
            return transformed_data
            
        except Exception as e:
            logger.error(
                "Data transformation failed",
                error=str(e),
                source_data=source_data
            )
            raise
    
    def _extract_value(
        self, 
        data: Dict[str, Any], 
        field: str, 
        path: Optional[str] = None
    ) -> Any:
        """Extract value from source data using field path"""
        if path:
            # Handle nested paths like "address.street"
            keys = path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        else:
            return data.get(field)
    
    def _set_value(
        self, 
        data: Dict[str, Any], 
        field: str, 
        path: Optional[str] = None, 
        value: Any = None
    ):
        """Set value in target data using field path"""
        if path:
            # Handle nested paths like "address.street"
            keys = path.split('.')
            current = data
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
        else:
            data[field] = value
    
    def _apply_transformation(
        self, 
        value: Any, 
        transformation_type: TransformationType, 
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Apply transformation to value"""
        if value is None:
            return None
        
        transformer = self.transformers.get(transformation_type)
        if transformer:
            return transformer(value, config or {})
        else:
            logger.warning(f"Unknown transformation type: {transformation_type}")
            return value
    
    def _no_transform(self, value: Any, config: Dict[str, Any]) -> Any:
        """No transformation - return value as is"""
        return value
    
    def _format_phone(self, value: str, config: Dict[str, Any]) -> str:
        """Format phone number"""
        if not value:
            return value
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', str(value))
        
        # Apply formatting based on config
        format_type = config.get('format', 'clean')
        
        if format_type == 'clean':
            return digits_only
        elif format_type == 'dashed':
            if len(digits_only) == 10:
                return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
            elif len(digits_only) == 11:
                return f"{digits_only[:1]}-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:]}"
        elif format_type == 'parentheses':
            if len(digits_only) == 10:
                return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        
        return digits_only
    
    def _format_date(self, value: str, config: Dict[str, Any]) -> str:
        """Format date string"""
        if not value:
            return value
        
        try:
            # Parse input date
            input_format = config.get('input_format', '%Y-%m-%d')
            output_format = config.get('output_format', '%d/%m/%Y')
            
            if isinstance(value, str):
                parsed_date = datetime.strptime(value, input_format)
                return parsed_date.strftime(output_format)
            else:
                return value
        except Exception as e:
            logger.warning(f"Date formatting failed: {e}")
            return value
    
    def _format_currency(self, value: Union[str, int, float], config: Dict[str, Any]) -> str:
        """Format currency value"""
        if value is None:
            return value
        
        try:
            # Convert to float
            numeric_value = float(value)
            
            # Apply formatting
            decimal_places = config.get('decimal_places', 2)
            include_symbol = config.get('include_symbol', False)
            symbol = config.get('symbol', '$')
            
            formatted = f"{numeric_value:.{decimal_places}f}"
            
            if include_symbol:
                formatted = f"{symbol}{formatted}"
            
            return formatted
        except Exception as e:
            logger.warning(f"Currency formatting failed: {e}")
            return str(value)
    
    def _split_name(self, value: str, config: Dict[str, Any]) -> Dict[str, str]:
        """Split full name into first and last name"""
        if not value:
            return {}
        
        parts = value.strip().split()
        
        if len(parts) == 1:
            return {'first_name': parts[0], 'last_name': ''}
        elif len(parts) == 2:
            return {'first_name': parts[0], 'last_name': parts[1]}
        else:
            # Handle multiple middle names
            first_name = parts[0]
            last_name = ' '.join(parts[1:])
            return {'first_name': first_name, 'last_name': last_name}
    
    def _object_mapping(self, value: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Map object fields according to configuration"""
        if not isinstance(value, dict):
            return value
        
        mapping = config.get('mapping', {})
        result = {}
        
        for source_key, target_key in mapping.items():
            if source_key in value:
                result[target_key] = value[source_key]
        
        return result
    
    def _array_format(self, value: List[Any], config: Dict[str, Any]) -> List[Any]:
        """Format array values"""
        if not isinstance(value, list):
            return value
        
        format_type = config.get('format', 'none')
        
        if format_type == 'phone_clean':
            return [self._format_phone(str(item), {'format': 'clean'}) for item in value]
        elif format_type == 'unique':
            return list(set(value))
        elif format_type == 'sorted':
            return sorted(value)
        
        return value
    
    def _conditional_transform(self, value: Any, config: Dict[str, Any]) -> Any:
        """Apply conditional transformation"""
        conditions = config.get('conditions', {})
        
        # Check if value matches any condition
        for condition_value, target_value in conditions.items():
            if str(value).lower() == str(condition_value).lower():
                return target_value
        
        # Return default value if no condition matches
        return config.get('default', value)
    
    def _custom_transform(self, value: Any, config: Dict[str, Any]) -> Any:
        """Apply custom transformation using provided function or rules"""
        # This would typically involve executing custom code or rules
        # For now, return the value as is
        logger.warning("Custom transformation not implemented")
        return value
    
    def _validate_value(self, value: Any, mapping: FieldMapping) -> bool:
        """Validate transformed value according to mapping rules"""
        if value is None and mapping.is_required:
            return False
        
        validation_rules = mapping.validation_rules
        if not validation_rules:
            return True
        
        # Check data type
        expected_type = validation_rules.get('type')
        if expected_type:
            if expected_type == 'email' and not self._is_valid_email(value):
                return False
            elif expected_type == 'phone' and not self._is_valid_phone(value):
                return False
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                return False
        
        # Check length constraints
        min_length = validation_rules.get('min_length')
        max_length = validation_rules.get('max_length')
        
        if min_length and len(str(value)) < min_length:
            return False
        if max_length and len(str(value)) > max_length:
            return False
        
        # Check value constraints
        min_value = validation_rules.get('min_value')
        max_value = validation_rules.get('max_value')
        
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        
        return True
    
    def _is_valid_email(self, value: str) -> bool:
        """Validate email format"""
        if not value:
            return False
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))
    
    def _is_valid_phone(self, value: str) -> bool:
        """Validate phone number format"""
        if not value:
            return False
        # Remove all non-digit characters and check length
        digits_only = re.sub(r'\D', '', str(value))
        return len(digits_only) >= 10
    
    def create_sample_mapping(self, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create sample field mappings based on source data structure"""
        mappings = []
        
        for key, value in source_data.items():
            mapping = {
                'source_field': key,
                'target_field': key,
                'transformation_type': TransformationType.NONE,
                'is_required': False,
                'data_type': self._infer_data_type(value)
            }
            mappings.append(mapping)
        
        return mappings
    
    def _infer_data_type(self, value: Any) -> DataType:
        """Infer data type from value"""
        if isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, (int, float)):
            return DataType.NUMBER
        elif isinstance(value, list):
            return DataType.ARRAY
        elif isinstance(value, dict):
            return DataType.OBJECT
        elif isinstance(value, str):
            # Try to infer specific string types
            if self._is_valid_email(value):
                return DataType.EMAIL
            elif self._is_valid_phone(value):
                return DataType.PHONE
            elif re.match(r'^\d+\.?\d*$', value):
                return DataType.CURRENCY
            else:
                return DataType.STRING
        else:
            return DataType.STRING
