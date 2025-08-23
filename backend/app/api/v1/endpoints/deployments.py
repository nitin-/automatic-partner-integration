from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import zipfile
import tempfile
from pathlib import Path

from ....core.database import get_db
from ....models.generated_api import GeneratedAPI
from ....models.lender import Lender
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
