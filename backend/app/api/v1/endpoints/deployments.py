from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import zipfile
import tempfile
import datetime
import uuid
from pathlib import Path

from ....core.database import get_db
from ....models.generated_api import GeneratedAPI
from ....models.lender import Lender
from ....models.deployed_api import DeployedAPI, DeployedIntegration
from ....schemas.common import ResponseModel, PaginationParams
from ....services.deployment_generator import DeploymentGenerator
from ....services.api_generator import APIGenerator
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/generate-deployment")
async def generate_deployment_package(
    generated_api_id: int,
    deployment_type: str = "docker",
    config: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate deployment package for a generated API"""
    try:
        # Get the generated API
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Initialize deployment generator
        deployment_gen = DeploymentGenerator()
        
        # Generate deployment package
        deployment_info = await deployment_gen.generate_deployment_package(
            generated_api=generated_api,
            deployment_type=deployment_type,
            config=config or {}
        )
        
        logger.info(
            "Deployment package generated successfully",
            generated_api_id=generated_api_id,
            deployment_type=deployment_type,
            deployment_dir=deployment_info["deployment_dir"]
        )
        
        return ResponseModel(
            success=True,
            message="Deployment package generated successfully",
            data={
                "deployment_dir": deployment_info["deployment_dir"],
                "files": deployment_info["files"],
                "generated_api_id": generated_api_id,
                "deployment_type": deployment_type
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to generate deployment package",
            generated_api_id=generated_api_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate deployment package: {str(e)}"
        )


@router.get("/download-deployment/{generated_api_id}")
async def download_deployment_package(
    generated_api_id: int,
    deployment_type: str = "docker",
    db: AsyncSession = Depends(get_db)
):
    """Download deployment package as ZIP file"""
    try:
        # Get the generated API
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Check if deployment directory exists
        deployment_dir = os.path.join(
            "generated_apis",
            f"deployment_{generated_api_id}"
        )
        
        if not os.path.exists(deployment_dir):
            # Generate deployment package first
            deployment_gen = DeploymentGenerator()
            deployment_info = await deployment_gen.generate_deployment_package(
                generated_api=generated_api,
                deployment_type=deployment_type,
                config={}
            )
            deployment_dir = deployment_info["deployment_dir"]
        
        # Create ZIP file
        zip_filename = f"{generated_api.name.lower().replace(' ', '_')}_{deployment_type}_deployment.zip"
        zip_path = os.path.join("generated_apis", zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(deployment_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, deployment_dir)
                    zipf.write(file_path, arcname)
        
        # Return file response
        from fastapi.responses import FileResponse
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type='application/zip'
        )
        
    except Exception as e:
        logger.error(
            "Failed to download deployment package",
            generated_api_id=generated_api_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download deployment package: {str(e)}"
        )


@router.post("/generate-helm-chart")
async def generate_helm_chart(
    generated_api_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate Helm chart for Kubernetes deployment"""
    try:
        # Get the generated API
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Initialize deployment generator
        deployment_gen = DeploymentGenerator()
        
        # Generate Helm chart
        chart_info = deployment_gen.generate_helm_chart(
            generated_api=generated_api,
            config=config or {}
        )
        
        logger.info(
            "Helm chart generated successfully",
            generated_api_id=generated_api_id,
            chart_dir=chart_info["chart_dir"]
        )
        
        return ResponseModel(
            success=True,
            message="Helm chart generated successfully",
            data={
                "chart_dir": chart_info["chart_dir"],
                "files": chart_info["files"],
                "generated_api_id": generated_api_id
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to generate Helm chart",
            generated_api_id=generated_api_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Helm chart: {str(e)}"
        )


@router.get("/deployment-templates")
async def get_deployment_templates():
    """Get available deployment templates"""
    templates = [
        {
            "type": "docker",
            "name": "Docker & Docker Compose",
            "description": "Containerized deployment with Docker and Docker Compose",
            "features": [
                "Easy local development",
                "Production-ready containers",
                "Built-in health checks",
                "Volume management"
            ]
        },
        {
            "type": "kubernetes",
            "name": "Kubernetes",
            "description": "Kubernetes deployment manifests",
            "features": [
                "Scalable deployment",
                "Service discovery",
                "ConfigMap and Secret management",
                "Ingress configuration"
            ]
        },
        {
            "type": "serverless",
            "name": "Serverless",
            "description": "Serverless deployment with AWS Lambda or similar",
            "features": [
                "Pay-per-use pricing",
                "Auto-scaling",
                "No server management",
                "Event-driven architecture"
            ]
        }
    ]
    
    return ResponseModel(
        success=True,
        message="Deployment templates retrieved successfully",
        data={"templates": templates}
    )


@router.get("/deployment-status/{generated_api_id}")
async def get_deployment_status(
    generated_api_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get deployment status for a generated API"""
    try:
        # Get the generated API
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Check deployment directories
        deployment_dirs = {
            "docker": os.path.join("generated_apis", f"deployment_{generated_api_id}"),
            "kubernetes": os.path.join("generated_apis", f"k8s_deployment_{generated_api_id}"),
            "helm": os.path.join("generated_apis", f"helm-chart_{generated_api_id}")
        }
        
        status = {}
        for deployment_type, dir_path in deployment_dirs.items():
            if os.path.exists(dir_path):
                files = os.listdir(dir_path) if os.path.isdir(dir_path) else []
                status[deployment_type] = {
                    "available": True,
                    "directory": dir_path,
                    "files": files,
                    "file_count": len(files)
                }
            else:
                status[deployment_type] = {
                    "available": False,
                    "directory": dir_path,
                    "files": [],
                    "file_count": 0
                }
        
        return ResponseModel(
            success=True,
            message="Deployment status retrieved successfully",
            data={
                "generated_api_id": generated_api_id,
                "status": status
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to get deployment status",
            generated_api_id=generated_api_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment status: {str(e)}"
        )


@router.delete("/cleanup-deployment/{generated_api_id}")
async def cleanup_deployment_files(
    generated_api_id: int,
    deployment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Clean up deployment files for a generated API"""
    try:
        # Get the generated API
        result = await db.execute(
            select(GeneratedAPI).where(GeneratedAPI.id == generated_api_id)
        )
        generated_api = result.scalar_one_or_none()
        
        if not generated_api:
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Define deployment directories to clean up
        deployment_dirs = []
        
        if deployment_type:
            if deployment_type == "docker":
                deployment_dirs.append(os.path.join("generated_apis", f"deployment_{generated_api_id}"))
            elif deployment_type == "kubernetes":
                deployment_dirs.append(os.path.join("generated_apis", f"k8s_deployment_{generated_api_id}"))
            elif deployment_type == "helm":
                deployment_dirs.append(os.path.join("generated_apis", f"helm-chart_{generated_api_id}"))
        else:
            # Clean up all deployment types
            deployment_dirs.extend([
                os.path.join("generated_apis", f"deployment_{generated_api_id}"),
                os.path.join("generated_apis", f"k8s_deployment_{generated_api_id}"),
                os.path.join("generated_apis", f"helm-chart_{generated_api_id}")
            ])
        
        cleaned_dirs = []
        for dir_path in deployment_dirs:
            if os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
                cleaned_dirs.append(dir_path)
        
        logger.info(
            "Deployment files cleaned up successfully",
            generated_api_id=generated_api_id,
            deployment_type=deployment_type,
            cleaned_dirs=cleaned_dirs
        )
        
        return ResponseModel(
            success=True,
            message="Deployment files cleaned up successfully",
            data={
                "generated_api_id": generated_api_id,
                "cleaned_dirs": cleaned_dirs
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to cleanup deployment files",
            generated_api_id=generated_api_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup deployment files: {str(e)}"
        )


@router.post("/deploy-integration")
async def deploy_integration(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Deploy an integration sequence as a production API"""
    # Extract parameters from request body
    lender_id = request.get("lender_id")
    sequence_config = request.get("sequence_config")
    field_mappings = request.get("field_mappings")
    
    if not lender_id:
        raise HTTPException(status_code=400, detail="lender_id is required")
    if not sequence_config:
        raise HTTPException(status_code=400, detail="sequence_config is required")
    if not field_mappings:
        raise HTTPException(status_code=400, detail="field_mappings is required")
    
    try:
        # Get the lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")
        
        # Validate sequence configuration
        if not sequence_config or not sequence_config.get("steps"):
            raise HTTPException(status_code=400, detail="Invalid sequence configuration")
        
        # Generate a unique deployment ID
        deployment_id = str(uuid.uuid4())
        
        # Generate API signature for the integration
        base_url = "http://localhost:8000"  # TODO: Get from config in production
        full_endpoint_url = f"{base_url}/api/v1/integrations/{deployment_id}"
        
        # Generate curl command for the integration
        integration_curl = f"curl -X POST '{full_endpoint_url}' \\\n  -H 'Content-Type: application/json' \\\n  -d '{{}}'"
        
        # Create deployment record in database
        deployed_integration = DeployedIntegration(
            id=deployment_id,
            lender_id=lender_id,
            sequence_config=sequence_config,
            field_mappings=field_mappings,
            api_signature={
                "method": "POST",
                "endpoint": full_endpoint_url,
                "curl_command": integration_curl,
                "description": f"Integration sequence for {lender.name} with {len(sequence_config.get('steps', []))} steps",
                "response_format": "JSON",
                "authentication": "None"
            },
            status="active"
        )
        
        db.add(deployed_integration)
        await db.commit()
        
        # Create response data
        deployment_info = {
            "id": deployment_id,
            "lender_id": lender_id,
            "lender_name": lender.name,
            "sequence_config": sequence_config,
            "field_mappings": field_mappings,
            "status": "deployed",
            "deployed_at": str(datetime.datetime.utcnow()),
            "endpoint_url": f"/api/v1/integrations/{deployment_id}",
            "full_endpoint_url": full_endpoint_url,
            "steps_count": len(sequence_config.get("steps", [])),
            "api_signature": deployed_integration.api_signature
        }
        
        logger.info(
            "Integration deployed successfully",
            deployment_id=deployment_id,
            lender_id=lender_id,
            steps_count=deployment_info["steps_count"]
        )
        
        return ResponseModel(
            success=True,
            message="Integration deployed successfully",
            data=deployment_info
        )
        
    except Exception as e:
        logger.error(
            "Failed to deploy integration",
            lender_id=lender_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy integration: {str(e)}"
        )


@router.post("/deploy-step-api")
async def deploy_step_api(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Deploy an individual integration step as a standalone API"""
    # Extract parameters from request body
    lender_id = request.get("lender_id")
    step_config = request.get("step_config")
    step_name = request.get("step_name")
    sequence_id = request.get("sequence_id")
    
    if not lender_id:
        raise HTTPException(status_code=400, detail="lender_id is required")
    if not step_config:
        raise HTTPException(status_code=400, detail="step_config is required")
    if not step_name:
        raise HTTPException(status_code=400, detail="step_name is required")
    
    try:
        # Get the lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")
        
        # Validate step configuration
        if not step_config:
            raise HTTPException(status_code=400, detail="Invalid step configuration")
        
        # Check for either step_type or integration_type (for backward compatibility)
        step_type = step_config.get("step_type") or step_config.get("integration_type")
        if not step_type:
            raise HTTPException(status_code=400, detail="Step configuration must have either 'step_type' or 'integration_type'")
        
        # Generate a unique step API ID
        step_api_id = str(uuid.uuid4())
        
        # Generate API signature and documentation
        base_url = "http://localhost:8000"  # TODO: Get from config in production
        full_endpoint_url = f"{base_url}/api/v1/steps/{step_api_id}"
        
        # Generate curl command
        http_method = step_config.get("http_method", "POST")
        headers = step_config.get("request_headers", {})
        request_schema = step_config.get("request_schema", {})
        
        # Build curl command
        curl_command = f"curl -X {http_method} '{full_endpoint_url}'"
        if headers:
            for key, value in headers.items():
                curl_command += f" \\\n  -H '{key}: {value}'"
        if request_schema and http_method in ["POST", "PUT", "PATCH"]:
            # Convert request schema to JSON example
            import json
            try:
                example_body = json.dumps(request_schema, indent=2)
                curl_command += f" \\\n  -H 'Content-Type: application/json' \\\n  -d '{example_body}'"
            except:
                curl_command += f" \\\n  -H 'Content-Type: application/json' \\\n  -d '{{}}'"
        
        # Create step API record in database
        deployed_api = DeployedAPI(
            id=step_api_id,
            lender_id=lender_id,
            step_name=step_name,
            step_config=step_config,
            api_signature={
                "method": http_method,
                "endpoint": full_endpoint_url,
                "curl_command": curl_command,
                "headers": headers,
                "request_schema": request_schema,
                "example_request": request_schema if request_schema else {},
                "response_format": "JSON",
                "authentication": "None" if step_config.get("auth_type") == "NONE" else step_config.get("auth_type", "Unknown")
            },
            status="active"
        )
        
        db.add(deployed_api)
        await db.commit()
        
        # Create response data
        step_api_info = {
            "id": step_api_id,
            "lender_id": lender_id,
            "lender_name": lender.name,
            "step_name": step_name,
            "step_config": step_config,
            "sequence_id": sequence_id,
            "status": "deployed",
            "deployed_at": str(datetime.datetime.utcnow()),
            "endpoint_url": f"/api/v1/steps/{step_api_id}",
            "full_endpoint_url": full_endpoint_url,
            "step_type": step_type,
            "description": step_config.get("description", ""),
            "api_signature": deployed_api.api_signature
        }
        
        logger.info(
            "Step API deployed successfully",
            step_api_id=step_api_id,
            lender_id=lender_id,
            step_name=step_name,
            step_type=step_type
        )
        
        return ResponseModel(
            success=True,
            message="Step API deployed successfully",
            data=step_api_info
        )
        
    except Exception as e:
        logger.error(
            "Failed to deploy step API",
            lender_id=lender_id,
            step_name=step_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy step API: {str(e)}"
        )


@router.get("/lender/{lender_id}/deployed-apis")
async def get_deployed_apis_for_lender(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all deployed APIs for a specific lender"""
    try:
        # Get the lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")
        
        # Get deployed APIs from database
        result = await db.execute(
            select(DeployedAPI).where(
                DeployedAPI.lender_id == lender_id,
                DeployedAPI.status == "active"
            ).order_by(DeployedAPI.deployed_at.desc())
        )
        deployed_apis = result.scalars().all()
        
        # Convert to response format
        api_list = []
        for api in deployed_apis:
            api_list.append({
                "id": api.id,
                "step_name": api.step_name,
                "step_config": api.step_config,
                "api_signature": api.api_signature,
                "status": api.status,
                "deployed_at": api.deployed_at.isoformat() if api.deployed_at else None,
                "last_executed_at": api.last_executed_at.isoformat() if api.last_executed_at else None,
                "execution_count": api.execution_count,
                "error_count": api.error_count
            })
        
        return ResponseModel(
            success=True,
            message=f"Retrieved {len(api_list)} deployed APIs for lender",
            data=api_list
        )
        
    except Exception as e:
        logger.error(
            "Failed to get deployed APIs for lender",
            lender_id=lender_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployed APIs: {str(e)}"
        )


@router.get("/lender/{lender_id}/integration-deployment")
async def get_integration_deployment_for_lender(
    lender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get integration deployment for a specific lender"""
    try:
        # Get the lender
        result = await db.execute(
            select(Lender).where(Lender.id == lender_id)
        )
        lender = result.scalar_one_or_none()
        
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")
        
        # Get integration deployment from database
        result = await db.execute(
            select(DeployedIntegration).where(
                DeployedIntegration.lender_id == lender_id,
                DeployedIntegration.status == "active"
            ).order_by(DeployedIntegration.deployed_at.desc())
        )
        integration_deployment = result.scalar_one_or_none()
        
        if not integration_deployment:
            return ResponseModel(
                success=True,
                message="No integration deployment found for this lender",
                data=None
            )
        
        # Convert to response format
        deployment_data = {
            "id": integration_deployment.id,
            "lender_id": integration_deployment.lender_id,
            "sequence_config": integration_deployment.sequence_config,
            "field_mappings": integration_deployment.field_mappings,
            "api_signature": integration_deployment.api_signature,
            "status": integration_deployment.status,
            "deployed_at": integration_deployment.deployed_at.isoformat() if integration_deployment.deployed_at else None,
            "last_executed_at": integration_deployment.last_executed_at.isoformat() if integration_deployment.last_executed_at else None,
            "execution_count": integration_deployment.execution_count,
            "error_count": integration_deployment.error_count
        }
        
        return ResponseModel(
            success=True,
            message="Integration deployment retrieved successfully",
            data=deployment_data
        )
        
    except Exception as e:
        logger.error(
            "Failed to get integration deployment for lender",
            lender_id=lender_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get integration deployment: {str(e)}"
        )


@router.delete("/step-api/{step_id}")
async def delete_step_api(
    step_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete/undeploy a step API"""
    try:
        # Get the deployed API
        result = await db.execute(
            select(DeployedAPI).where(DeployedAPI.id == step_id)
        )
        deployed_api = result.scalar_one_or_none()
        
        if not deployed_api:
            raise HTTPException(status_code=404, detail="Deployed API not found")
        
        # Soft delete by setting status to inactive
        deployed_api.status = "inactive"
        await db.commit()
        
        logger.info(
            "Step API deleted successfully",
            step_id=step_id,
            lender_id=deployed_api.lender_id
        )
        
        return ResponseModel(
            success=True,
            message="Step API deleted successfully",
            data={"id": step_id, "status": "deleted"}
        )
        
    except Exception as e:
        logger.error(
            "Failed to delete step API",
            step_id=step_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete step API: {str(e)}"
        )


@router.delete("/integration/{integration_id}")
async def delete_integration_deployment(
    integration_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete/undeploy an integration deployment"""
    try:
        # Get the deployed integration
        result = await db.execute(
            select(DeployedIntegration).where(DeployedIntegration.id == integration_id)
        )
        deployed_integration = result.scalar_one_or_none()
        
        if not deployed_integration:
            raise HTTPException(status_code=404, detail="Integration deployment not found")
        
        # Soft delete by setting status to inactive
        deployed_integration.status = "inactive"
        await db.commit()
        
        logger.info(
            "Integration deployment deleted successfully",
            integration_id=integration_id,
            lender_id=deployed_integration.lender_id
        )
        
        return ResponseModel(
            success=True,
            message="Integration deployment deleted successfully",
            data={"id": integration_id, "status": "deleted"}
        )
        
    except Exception as e:
        logger.error(
            "Failed to delete integration deployment",
            integration_id=integration_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete integration deployment: {str(e)}"
        )
