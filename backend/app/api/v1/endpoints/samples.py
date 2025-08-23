from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....services.sample_configs import SampleConfigGenerator
from ....services.integration_service import IntegrationService
from ....schemas.common import ResponseModel
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/sample-lenders")
async def get_sample_lenders() -> ResponseModel[List[Dict[str, Any]]]:
    """Get sample lender configurations for testing"""
    try:
        sample_lenders = SampleConfigGenerator.get_sample_lenders()
        return ResponseModel(
            success=True,
            data=sample_lenders,
            message="Sample lenders retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get sample lenders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sample lenders")


@router.get("/sample-lenders/{lender_name}")
async def get_sample_lender_config(lender_name: str) -> ResponseModel[Dict[str, Any]]:
    """Get specific sample lender configuration"""
    try:
        sample_lenders = SampleConfigGenerator.get_sample_lenders()
        
        # Find the requested lender
        lender_config = None
        for lender in sample_lenders:
            if lender["name"].lower() == lender_name.lower():
                lender_config = lender
                break
        
        if not lender_config:
            raise HTTPException(status_code=404, detail=f"Sample lender '{lender_name}' not found")
        
        return ResponseModel(
            success=True,
            data=lender_config,
            message=f"Sample lender '{lender_name}' configuration retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sample lender config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sample lender configuration")


@router.get("/sample-lenders/{lender_name}/test-data")
async def get_sample_test_data(lender_name: str) -> ResponseModel[Dict[str, Any]]:
    """Get appropriate test data for a sample lender"""
    try:
        test_data = SampleConfigGenerator.get_test_data_for_lender(lender_name)
        
        return ResponseModel(
            success=True,
            data=test_data,
            message=f"Test data for '{lender_name}' retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get test data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get test data")


@router.post("/sample-lenders/{lender_name}/test")
async def test_sample_lender(
    lender_name: str,
    test_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Test a sample lender configuration with provided data"""
    try:
        # Get sample lender configuration
        sample_lenders = SampleConfigGenerator.get_sample_lenders()
        lender_config = None
        
        for lender in sample_lenders:
            if lender["name"].lower() == lender_name.lower():
                lender_config = lender
                break
        
        if not lender_config:
            raise HTTPException(status_code=404, detail=f"Sample lender '{lender_name}' not found")
        
        # Simulate the integration process
        integration_service = IntegrationService()
        
        # Transform data using field mappings
        from ....services.transformer import DataTransformer
        transformer = DataTransformer()
        
        # Create mock field mappings for testing
        field_mappings = []
        for mapping_config in lender_config["field_mappings"]:
            from ....models.field_mapping import FieldMapping
            mapping = FieldMapping(
                source_field=mapping_config["source_field"],
                target_field=mapping_config["target_field"],
                transformation_type=mapping_config["transformation_type"],
                transformation_config=mapping_config["transformation_config"],
                is_required=mapping_config["is_required"],
                is_active=mapping_config["is_active"]
            )
            field_mappings.append(mapping)
        
        # Transform the test data
        transformed_data = transformer.transform_data(test_data, field_mappings)
        
        # Simulate API call (mock response)
        mock_response = {
            "status_code": 200,
            "success": True,
            "data": {
                "lead_id": f"lead_{lender_name.lower().replace(' ', '_')}_12345",
                "status": "submitted",
                "message": "Lead submitted successfully"
            },
            "duration_ms": 150,
            "headers": {"content-type": "application/json"}
        }
        
        # If there's a sequence, simulate sequence execution
        sequence_result = None
        if lender_config.get("integration_sequence"):
            sequence = lender_config["integration_sequence"]
            sequence_result = {
                "sequence_id": f"seq_{lender_name.lower().replace(' ', '_')}",
                "sequence_name": sequence["name"],
                "execution_mode": sequence["execution_mode"],
                "steps": [],
                "final_result": transformed_data,
                "success": True,
                "error": None
            }
            
            # Simulate each step
            for step in sequence["steps"]:
                step_result = {
                    "step_id": f"step_{step['sequence_order']}",
                    "step_name": step["name"],
                    "step_order": step["sequence_order"],
                    "input_data": transformed_data,
                    "output_data": {
                        "status": "success",
                        "step_id": f"step_{step['sequence_order']}",
                        "timestamp": "2024-01-15T10:30:00Z"
                    },
                    "success": True,
                    "error": None,
                    "duration_ms": 100 + (step["sequence_order"] * 50)
                }
                sequence_result["steps"].append(step_result)
        
        result = {
            "lender_name": lender_config["name"],
            "integration_pattern": lender_config["integration_pattern"],
            "input_data": test_data,
            "transformed_data": transformed_data,
            "api_response": mock_response,
            "sequence_result": sequence_result,
            "field_mappings_used": len(field_mappings),
            "transformation_count": len([m for m in field_mappings if m.transformation_type != "none"])
        }
        
        return ResponseModel(
            success=True,
            data=result,
            message=f"Sample lender '{lender_name}' test completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test sample lender: {e}")
        raise HTTPException(status_code=500, detail="Failed to test sample lender")


@router.post("/sample-lenders/{lender_name}/create")
async def create_sample_lender(
    lender_name: str,
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Create a real lender from sample configuration"""
    try:
        # Get sample lender configuration
        sample_lenders = SampleConfigGenerator.get_sample_lenders()
        lender_config = None
        
        for lender in sample_lenders:
            if lender["name"].lower() == lender_name.lower():
                lender_config = lender
                break
        
        if not lender_config:
            raise HTTPException(status_code=404, detail=f"Sample lender '{lender_name}' not found")
        
        # Create the lender
        from ....models.lender import Lender
        from ....models.field_mapping import FieldMapping
        from ....models.integration import Integration, IntegrationSequence
        
        # Create lender
        lender = Lender(
            name=lender_config["name"],
            description=lender_config["description"],
            contact_email=lender_config["contact_email"],
            contact_phone=lender_config["contact_phone"],
            status=lender_config["status"],
            is_active=True
        )
        
        db.add(lender)
        await db.flush()  # Get the lender ID
        
        # Create field mappings
        for mapping_config in lender_config["field_mappings"]:
            field_mapping = FieldMapping(
                lender_id=lender.id,
                name=mapping_config["name"],
                source_field=mapping_config["source_field"],
                target_field=mapping_config["target_field"],
                transformation_type=mapping_config["transformation_type"],
                transformation_config=mapping_config["transformation_config"],
                is_required=mapping_config["is_required"],
                is_active=mapping_config["is_active"]
            )
            db.add(field_mapping)
        
        # Create integration sequence
        if lender_config.get("integration_sequence"):
            seq_config = lender_config["integration_sequence"]
            sequence = IntegrationSequence(
                lender_id=lender.id,
                name=seq_config["name"],
                description=seq_config["description"],
                sequence_type=seq_config["sequence_type"],
                execution_mode=seq_config["execution_mode"],
                stop_on_error=seq_config["stop_on_error"],
                retry_failed_steps=seq_config["retry_failed_steps"],
                is_active=seq_config["is_active"]
            )
            
            db.add(sequence)
            await db.flush()  # Get the sequence ID
            
            # Create integration steps
            for step_config in seq_config["steps"]:
                integration = Integration(
                    lender_id=lender.id,
                    parent_sequence_id=sequence.id,
                    name=step_config["name"],
                    integration_type=step_config["integration_type"],
                    api_endpoint=step_config["api_endpoint"],
                    http_method=step_config["http_method"],
                    sequence_order=step_config["sequence_order"],
                    auth_type=step_config["auth_type"],
                    auth_config=step_config["auth_config"],
                    depends_on_fields=step_config["depends_on_fields"],
                    output_fields=step_config["output_fields"],
                    is_sequence_step=True,
                    is_active=step_config.get("is_active", True)
                )
                db.add(integration)
        
        await db.commit()
        
        return ResponseModel(
            success=True,
            data={
                "lender_id": lender.id,
                "lender_name": lender.name,
                "field_mappings_created": len(lender_config["field_mappings"]),
                "sequence_created": bool(lender_config.get("integration_sequence"))
            },
            message=f"Sample lender '{lender_name}' created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create sample lender: {e}")
        raise HTTPException(status_code=500, detail="Failed to create sample lender")


@router.get("/sample-lenders/{lender_name}/field-mappings")
async def get_sample_field_mappings(lender_name: str) -> ResponseModel[List[Dict[str, Any]]]:
    """Get field mappings for a specific sample lender"""
    try:
        sample_lenders = SampleConfigGenerator.get_sample_lenders()
        
        # Find the requested lender
        lender_config = None
        for lender in sample_lenders:
            if lender["name"].lower() == lender_name.lower():
                lender_config = lender
                break
        
        if not lender_config:
            raise HTTPException(status_code=404, detail=f"Sample lender '{lender_name}' not found")
        
        return ResponseModel(
            success=True,
            data=lender_config["field_mappings"],
            message=f"Field mappings for '{lender_name}' retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get field mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get field mappings")


@router.get("/sample-lenders/{lender_name}/sequence")
async def get_sample_sequence(lender_name: str) -> ResponseModel[Dict[str, Any]]:
    """Get integration sequence for a specific sample lender"""
    try:
        sample_lenders = SampleConfigGenerator.get_sample_lenders()
        
        # Find the requested lender
        lender_config = None
        for lender in sample_lenders:
            if lender["name"].lower() == lender_name.lower():
                lender_config = lender
                break
        
        if not lender_config:
            raise HTTPException(status_code=404, detail=f"Sample lender '{lender_name}' not found")
        
        sequence = lender_config.get("integration_sequence")
        if not sequence:
            raise HTTPException(status_code=404, detail=f"No sequence found for '{lender_name}'")
        
        return ResponseModel(
            success=True,
            data=sequence,
            message=f"Integration sequence for '{lender_name}' retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sequence")
