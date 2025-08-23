import os
import json
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import jinja2
from ..core.config import settings
from ..models.generated_api import GeneratedAPI
from ..models.lender import Lender
import structlog

logger = structlog.get_logger()


class DeploymentGenerator:
    """Service for generating deployment configurations for API suites"""
    
    def __init__(self):
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(settings.TEMPLATES_DIR),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    async def generate_deployment_package(
        self,
        generated_api: GeneratedAPI,
        deployment_type: str = "docker",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate deployment package for a generated API"""
        try:
            # Read the generated API file
            with open(generated_api.file_path, 'r', encoding='utf-8') as f:
                api_content = f.read()
            
            # Create deployment directory
            deployment_dir = os.path.join(
                settings.GENERATED_APIS_DIR,
                f"deployment_{generated_api.id}"
            )
            os.makedirs(deployment_dir, exist_ok=True)
            
            # Generate deployment files based on type
            if deployment_type == "docker":
                files = await self._generate_docker_deployment(
                    generated_api, api_content, deployment_dir, config
                )
            elif deployment_type == "kubernetes":
                files = await self._generate_kubernetes_deployment(
                    generated_api, api_content, deployment_dir, config
                )
            elif deployment_type == "serverless":
                files = await self._generate_serverless_deployment(
                    generated_api, api_content, deployment_dir, config
                )
            else:
                raise ValueError(f"Unsupported deployment type: {deployment_type}")
            
            # Generate README
            readme_content = self._generate_readme(generated_api, deployment_type, config)
            files['README.md'] = readme_content
            
            # Write all files
            for filename, content in files.items():
                file_path = os.path.join(deployment_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(
                "Deployment package generated successfully",
                generated_api_id=generated_api.id,
                deployment_type=deployment_type,
                deployment_dir=deployment_dir
            )
            
            return {
                "deployment_dir": deployment_dir,
                "files": list(files.keys())
            }
            
        except Exception as e:
            logger.error(
                "Failed to generate deployment package",
                generated_api_id=generated_api.id,
                error=str(e)
            )
            raise
    
    async def _generate_docker_deployment(
        self,
        generated_api: GeneratedAPI,
        api_content: str,
        deployment_dir: str,
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate Docker deployment files"""
        files = {}
        
        # Dockerfile
        dockerfile_template = self.template_env.get_template('dockerfile.j2')
        files['Dockerfile'] = dockerfile_template.render({
            "language": generated_api.language,
            "framework": generated_api.framework,
            "dependencies": generated_api.dependencies or [],
            "api_content": api_content,
            "config": config or {}
        })
        
        # docker-compose.yml
        compose_template = self.template_env.get_template('docker-compose.yml.j2')
        files['docker-compose.yml'] = compose_template.render({
            "api_name": generated_api.name.lower().replace(' ', '_'),
            "language": generated_api.language,
            "framework": generated_api.framework,
            "port": config.get('port', 8000) if config else 8000,
            "config": config or {}
        })
        
        # .dockerignore
        files['.dockerignore'] = self._generate_dockerignore(generated_api.language)
        
        # requirements.txt (for Python)
        if generated_api.language == 'python':
            files['requirements.txt'] = self._generate_requirements_txt(
                generated_api.dependencies or []
            )
        
        # package.json (for Node.js)
        if generated_api.language in ['javascript', 'typescript']:
            files['package.json'] = self._generate_package_json(
                generated_api.name,
                generated_api.dependencies or [],
                generated_api.language
            )
        
        return files
    
    async def _generate_kubernetes_deployment(
        self,
        generated_api: GeneratedAPI,
        api_content: str,
        deployment_dir: str,
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate Kubernetes deployment files"""
        files = {}
        
        # Deployment YAML
        deployment_template = self.template_env.get_template('k8s-deployment.yaml.j2')
        files['deployment.yaml'] = deployment_template.render({
            "api_name": generated_api.name.lower().replace(' ', '-'),
            "language": generated_api.language,
            "framework": generated_api.framework,
            "replicas": config.get('replicas', 1) if config else 1,
            "port": config.get('port', 8000) if config else 8000,
            "config": config or {}
        })
        
        # Service YAML
        service_template = self.template_env.get_template('k8s-service.yaml.j2')
        files['service.yaml'] = service_template.render({
            "api_name": generated_api.name.lower().replace(' ', '-'),
            "port": config.get('port', 8000) if config else 8000,
            "config": config or {}
        })
        
        # ConfigMap YAML
        configmap_template = self.template_env.get_template('k8s-configmap.yaml.j2')
        files['configmap.yaml'] = configmap_template.render({
            "api_name": generated_api.name.lower().replace(' ', '-'),
            "config": config or {}
        })
        
        # Ingress YAML (if specified)
        if config and config.get('ingress'):
            ingress_template = self.template_env.get_template('k8s-ingress.yaml.j2')
            files['ingress.yaml'] = ingress_template.render({
                "api_name": generated_api.name.lower().replace(' ', '-'),
                "host": config['ingress'].get('host', ''),
                "config": config or {}
            })
        
        return files
    
    async def _generate_serverless_deployment(
        self,
        generated_api: GeneratedAPI,
        api_content: str,
        deployment_dir: str,
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate serverless deployment files"""
        files = {}
        
        # Serverless framework config
        serverless_template = self.template_env.get_template('serverless.yml.j2')
        files['serverless.yml'] = serverless_template.render({
            "api_name": generated_api.name.lower().replace(' ', '-'),
            "language": generated_api.language,
            "framework": generated_api.framework,
            "config": config or {}
        })
        
        # Handler file
        handler_template = self.template_env.get_template('serverless-handler.py.j2')
        files['handler.py'] = handler_template.render({
            "api_content": api_content,
            "language": generated_api.language,
            "config": config or {}
        })
        
        return files
    
    def _generate_readme(
        self,
        generated_api: GeneratedAPI,
        deployment_type: str,
        config: Optional[Dict[str, Any]]
    ) -> str:
        """Generate README for deployment package"""
        readme_template = self.template_env.get_template('deployment-readme.md.j2')
        return readme_template.render({
            "api_name": generated_api.name,
            "description": generated_api.description,
            "language": generated_api.language,
            "framework": generated_api.framework,
            "deployment_type": deployment_type,
            "config": config or {},
            "generated_at": generated_api.created_at
        })
    
    def _generate_dockerignore(self, language: str) -> str:
        """Generate .dockerignore file"""
        ignore_patterns = {
            "python": [
                "__pycache__",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                ".Python",
                "env",
                "pip-log.txt",
                "pip-delete-this-directory.txt",
                ".tox",
                ".coverage",
                ".coverage.*",
                ".cache",
                "nosetests.xml",
                "coverage.xml",
                "*.cover",
                "*.log",
                ".git",
                ".mypy_cache",
                ".pytest_cache",
                ".hypothesis"
            ],
            "javascript": [
                "node_modules",
                "npm-debug.log",
                "yarn-debug.log",
                "yarn-error.log",
                ".git",
                ".gitignore",
                "README.md",
                "Dockerfile",
                ".dockerignore",
                ".env",
                ".env.local",
                ".env.development.local",
                ".env.test.local",
                ".env.production.local"
            ],
            "typescript": [
                "node_modules",
                "npm-debug.log",
                "yarn-debug.log",
                "yarn-error.log",
                ".git",
                ".gitignore",
                "README.md",
                "Dockerfile",
                ".dockerignore",
                ".env",
                ".env.local",
                ".env.development.local",
                ".env.test.local",
                ".env.production.local",
                "dist",
                "build"
            ]
        }
        
        patterns = ignore_patterns.get(language, [])
        return "\n".join(patterns)
    
    def _generate_requirements_txt(self, dependencies: List[str]) -> str:
        """Generate requirements.txt for Python"""
        base_deps = [
            "fastapi>=0.104.1",
            "uvicorn[standard]>=0.24.0",
            "httpx>=0.25.2",
            "pydantic>=2.5.0",
        ]
        
        all_deps = base_deps + dependencies
        return "\n".join(all_deps)
    
    def _generate_package_json(
        self,
        name: str,
        dependencies: List[str],
        language: str
    ) -> str:
        """Generate package.json for Node.js"""
        package_data = {
            "name": name.lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": f"Generated API client for {name}",
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "dev": "nodemon index.js",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.18.2",
                "axios": "^1.4.0",
                "cors": "^2.8.5",
                "helmet": "^7.0.0"
            },
            "devDependencies": {
                "nodemon": "^3.0.1",
                "jest": "^29.5.0"
            },
            "engines": {
                "node": ">=18.0.0"
            }
        }
        
        # Add custom dependencies
        for dep in dependencies:
            if isinstance(dep, str):
                package_data["dependencies"][dep] = "latest"
            elif isinstance(dep, dict):
                package_data["dependencies"].update(dep)
        
        return json.dumps(package_data, indent=2)
    
    def generate_helm_chart(
        self,
        generated_api: GeneratedAPI,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate Helm chart for Kubernetes deployment"""
        chart_dir = os.path.join(
            settings.GENERATED_APIS_DIR,
            f"helm-chart_{generated_api.id}"
        )
        os.makedirs(chart_dir, exist_ok=True)
        
        # Chart.yaml
        chart_yaml = {
            "apiVersion": "v2",
            "name": generated_api.name.lower().replace(' ', '-'),
            "description": f"Helm chart for {generated_api.name}",
            "type": "application",
            "version": "0.1.0",
            "appVersion": "1.0.0"
        }
        
        # values.yaml
        values_yaml = {
            "replicaCount": 1,
            "image": {
                "repository": f"{generated_api.name.lower().replace(' ', '-')}",
                "tag": "latest",
                "pullPolicy": "IfNotPresent"
            },
            "service": {
                "type": "ClusterIP",
                "port": 8000
            },
            "ingress": {
                "enabled": False,
                "className": "",
                "annotations": {},
                "hosts": []
            },
            "resources": {
                "limits": {
                    "cpu": "500m",
                    "memory": "512Mi"
                },
                "requests": {
                    "cpu": "250m",
                    "memory": "256Mi"
                }
            }
        }
        
        # Update with custom config
        if config:
            values_yaml.update(config)
        
        files = {
            "Chart.yaml": yaml.dump(chart_yaml, default_flow_style=False),
            "values.yaml": yaml.dump(values_yaml, default_flow_style=False),
        }
        
        # Write files
        for filename, content in files.items():
            file_path = os.path.join(chart_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return {
            "chart_dir": chart_dir,
            "files": list(files.keys())
        }
