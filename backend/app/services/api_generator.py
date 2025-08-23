import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
import jinja2
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.config import settings
from ..models.lender import Lender
from ..models.api_config import APIConfig
from ..models.api_template import APITemplate
from ..models.generated_api import GeneratedAPI
import structlog

logger = structlog.get_logger()


class APIGenerator:
    """Service for generating API integration code"""
    
    def __init__(self):
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(settings.TEMPLATES_DIR),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.template_env.filters['to_json'] = json.dumps
        self.template_env.filters['to_yaml'] = yaml.dump
        self.template_env.filters['snake_case'] = self._to_snake_case
        self.template_env.filters['camel_case'] = self._to_camel_case
        self.template_env.filters['pascal_case'] = self._to_pascal_case
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()
    
    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase"""
        import re
        words = re.split(r'[_\s-]+', text)
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        import re
        words = re.split(r'[_\s-]+', text)
        return ''.join(word.capitalize() for word in words)
    
    async def generate_api_client(
        self,
        db: AsyncSession,
        lender_id: int,
        template_id: Optional[int] = None,
        language: str = "python",
        framework: str = "fastapi",
        config: Optional[Dict[str, Any]] = None
    ) -> GeneratedAPI:
        """Generate API client for a lender"""
        start_time = time.time()
        
        try:
            # Get lender and configurations
            lender_result = await db.execute(
                select(Lender).where(Lender.id == lender_id)
            )
            lender = lender_result.scalar_one_or_none()
            
            if not lender:
                raise ValueError(f"Lender with ID {lender_id} not found")
            
            # Get API configurations
            configs_result = await db.execute(
                select(APIConfig).where(APIConfig.lender_id == lender_id)
            )
            api_configs = configs_result.scalars().all()
            
            if not api_configs:
                raise ValueError(f"No API configurations found for lender {lender.name}")
            
            # Get template
            template = None
            if template_id:
                template_result = await db.execute(
                    select(APITemplate).where(APITemplate.id == template_id)
                )
                template = template_result.scalar_one_or_none()
            
            if not template:
                # Use default template for language/framework
                template_result = await db.execute(
                    select(APITemplate).where(
                        APITemplate.template_type == f"jinja2_{language}",
                        APITemplate.is_active == True
                    ).order_by(APITemplate.is_system_template.desc())
                )
                template = template_result.scalar_one_or_none()
            
            if not template:
                raise ValueError(f"No suitable template found for {language}/{framework}")
            
            # Prepare template context
            context = self._prepare_template_context(lender, api_configs, config)
            
            # Generate code
            generated_code = self._render_template(template, context)
            
            # Calculate file hash
            file_hash = hashlib.sha256(generated_code.encode()).hexdigest()
            
            # Determine file path and extension
            file_extension = template.file_extension or self._get_file_extension(language)
            file_name = f"{lender.name.lower().replace(' ', '_')}_client{file_extension}"
            file_path = os.path.join(settings.GENERATED_APIS_DIR, file_name)
            
            # Write generated code to file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            
            # Create GeneratedAPI record
            generation_time = time.time() - start_time
            generated_api = GeneratedAPI(
                lender_id=lender_id,
                name=f"{lender.name} API Client",
                description=f"Generated API client for {lender.name}",
                version="1.0.0",
                template_id=template.id,
                generation_config=config,
                file_path=file_path,
                file_size=len(generated_code),
                file_hash=file_hash,
                language=language,
                framework=framework,
                dependencies=template.dependencies,
                is_valid=True,
                test_status="pending",
                generation_time=generation_time
            )
            
            db.add(generated_api)
            await db.commit()
            await db.refresh(generated_api)
            
            # Update template usage statistics
            template.usage_count += 1
            template.last_used_at = time.time()
            await db.commit()
            
            logger.info(
                "API client generated successfully",
                lender_id=lender_id,
                lender_name=lender.name,
                language=language,
                framework=framework,
                generation_time=generation_time,
                file_size=len(generated_code)
            )
            
            return generated_api
            
        except Exception as e:
            await db.rollback()
            logger.error(
                "Failed to generate API client",
                lender_id=lender_id,
                error=str(e)
            )
            raise
    
    def _prepare_template_context(
        self,
        lender: Lender,
        api_configs: List[APIConfig],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare context for template rendering"""
        context = {
            "lender": {
                "name": lender.name,
                "description": lender.description,
                "base_url": str(lender.base_url),
                "api_version": lender.api_version,
                "auth_type": lender.auth_type,
                "auth_config": lender.auth_config or {},
                "rate_limit": lender.rate_limit,
                "timeout": lender.timeout,
                "contact_email": lender.contact_email,
                "support_url": str(lender.support_url) if lender.support_url else None
            },
            "api_configs": [
                {
                    "name": config.name,
                    "description": config.description,
                    "endpoint_path": config.endpoint_path,
                    "method": config.method,
                    "headers": config.headers or {},
                    "query_params": config.query_params or {},
                    "request_body_schema": config.request_body_schema or {},
                    "response_schema": config.response_schema or {},
                    "success_codes": config.success_codes or [200, 201],
                    "requires_auth": config.requires_auth,
                    "auth_parameters": config.auth_parameters or {},
                    "rate_limit": config.rate_limit,
                    "retry_config": config.retry_config or {},
                    "validation_rules": config.validation_rules or {},
                    "data_mapping": config.data_mapping or {},
                    "version": config.version
                }
                for config in api_configs
            ],
            "config": config or {},
            "generation_timestamp": time.time(),
            "utils": {
                "to_snake_case": self._to_snake_case,
                "to_camel_case": self._to_camel_case,
                "to_pascal_case": self._to_pascal_case
            }
        }
        
        return context
    
    def _render_template(self, template: APITemplate, context: Dict[str, Any]) -> str:
        """Render template with context"""
        try:
            jinja_template = self.template_env.from_string(template.template_content)
            return jinja_template.render(**context)
        except Exception as e:
            logger.error("Template rendering failed", template_id=template.id, error=str(e))
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            "python": ".py",
            "typescript": ".ts",
            "javascript": ".js",
            "java": ".java",
            "csharp": ".cs",
            "go": ".go",
            "rust": ".rs"
        }
        return extensions.get(language, ".py")
    
    async def validate_generated_api(self, generated_api: GeneratedAPI) -> bool:
        """Validate generated API code"""
        try:
            # Read generated file
            with open(generated_api.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax validation based on language
            if generated_api.language == "python":
                import ast
                ast.parse(content)
            elif generated_api.language == "typescript":
                # Basic TypeScript validation (would need tsc in production)
                if "import" in content or "export" in content:
                    return True
            elif generated_api.language == "javascript":
                # Basic JavaScript validation
                if "function" in content or "const" in content or "let" in content:
                    return True
            
            return True
            
        except Exception as e:
            logger.error(
                "Generated API validation failed",
                generated_api_id=generated_api.id,
                error=str(e)
            )
            return False
    
    async def generate_openapi_spec(
        self,
        lender: Lender,
        api_configs: List[APIConfig]
    ) -> Dict[str, Any]:
        """Generate OpenAPI specification from lender and API configs"""
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": f"{lender.name} API",
                "description": lender.description or f"API for {lender.name}",
                "version": lender.api_version or "1.0.0",
                "contact": {
                    "email": lender.contact_email
                } if lender.contact_email else {}
            },
            "servers": [
                {
                    "url": str(lender.base_url),
                    "description": f"{lender.name} API server"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {},
                "schemas": {}
            }
        }
        
        # Add security schemes based on auth type
        if lender.auth_type == "bearer":
            openapi_spec["components"]["securitySchemes"]["bearerAuth"] = {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        elif lender.auth_type == "api_key":
            openapi_spec["components"]["securitySchemes"]["apiKeyAuth"] = {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        
        # Add paths from API configs
        for config in api_configs:
            path = config.endpoint_path
            method = config.method.lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            openapi_spec["paths"][path][method] = {
                "summary": config.name,
                "description": config.description,
                "parameters": [],
                "responses": {
                    str(code): {
                        "description": f"Success response for {code}"
                    }
                    for code in (config.success_codes or [200])
                }
            }
            
            # Add parameters
            if config.query_params:
                for param_name, param_info in config.query_params.items():
                    openapi_spec["paths"][path][method]["parameters"].append({
                        "name": param_name,
                        "in": "query",
                        "required": param_info.get("required", False),
                        "schema": {
                            "type": param_info.get("type", "string")
                        }
                    })
            
            # Add request body if needed
            if config.request_body_schema and method in ["post", "put", "patch"]:
                openapi_spec["paths"][path][method]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": config.request_body_schema
                        }
                    }
                }
        
        return openapi_spec
