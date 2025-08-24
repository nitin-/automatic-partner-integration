# Lead Generation API Integration Framework

A comprehensive framework for automating lender/partner API integrations in the lead generation business. This framework provides a visual backoffice interface for non-technical users to configure field mappings between your standard form data and various lender API requirements.

## 🎯 **Business Context**

- **Industry**: Lead generation for loan/insurance products
- **Problem**: Manual development cycle for each lender integration
- **Solution**: Visual field mapping interface for non-technical users
- **Outcome**: Automated API integrations without developer intervention

## 🚀 **Key Features**

### **Visual Field Mapping**
- **Drag-and-drop interface** for mapping your fields to lender fields
- **Support for complex data structures** (nested objects, arrays)
- **Real-time mapping validation** and testing
- **Template-based configurations** for similar lenders

### **Data Transformation Engine**
- **Format conversions**: Phone numbers, dates, currency
- **Conditional logic**: Different mappings based on loan type
- **Data validation**: Field validation rules and error handling
- **Nested object support**: Address, employment details, etc.

### **Lender Management**
- **Lender onboarding**: API endpoints, authentication, rate limits
- **Field mapping configuration**: Visual interface for non-technical users
- **Testing interface**: Validate integrations before going live
- **Monitoring dashboard**: Track API calls, success rates, errors

### **Integration Patterns**
- **Real-time lead submission**: Immediate API calls to lenders
- **Batch processing**: Status polling, bulk operations
- **Error handling**: Retry logic, fallback mechanisms
- **Rate limiting**: Respect lender API limits

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Flutter App     │    │ Your Backend    │    │ Integration     │
│ (Customer UI)   │───▶│ (Lead Data)     │───▶│ Framework       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ Lender APIs     │
                                              │ (Multiple)      │
                                              └─────────────────┘
```

### **Framework Components**

```
lead_integration_framework/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── transformers/   # Data transformation engine
│   ├── templates/          # Field mapping templates
│   └── alembic/            # Database migrations
├── frontend/               # React backoffice UI
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   └── mappers/        # Field mapping interface
├── generated_integrations/ # Generated API integrations
├── docker-compose.yml      # Development environment
├── start.sh               # Startup script with credential prompting
└── reset-docker-compose.sh # Reset script for docker-compose.yml
```

## 📋 **Core Entities**

### **1. Lender**
- Basic information (name, contact, description)
- API configuration (endpoints, authentication, rate limits)
- Field mapping templates
- Status (active/inactive)

### **2. Field Mapping**
- Source field (your standard field)
- Target field (lender's required field)
- Transformation rules (format, validation, conditional)
- Data type and structure

### **3. Integration Template**
- Reusable mapping configurations
- Common field transformations
- Industry-specific templates

### **4. API Configuration**
- HTTP method and endpoint
- Authentication details
- Request/response schemas
- Error handling rules

## 🔄 **Integration Workflow**

### **1. Lender Onboarding**
```
Product Team → Backoffice UI
├── Add lender details
├── Configure API endpoints
├── Set authentication (API keys)
├── Define rate limits
└── Create field mappings
```

### **2. Field Mapping Configuration**
```
Visual Interface
├── Your Fields          →  Lender Fields
│   ├── full_name       →  customer_name
│   ├── email           →  email_address
│   ├── phone           →  mobile_number
│   ├── address         →  {street, city, state}
│   └── loan_amount     →  requested_amount
```

### **3. Data Transformation**
```
Input Data              →  Transformation    →  Output Data
├── "John Doe"          →  Split name       →  {first: "John", last: "Doe"}
├── "+1-555-123-4567"   →  Format phone     →  "5551234567"
├── "50000"             →  Currency format  →  "50000.00"
└── "2024-01-15"        →  Date format      →  "15/01/2024"
```

### **4. API Integration**
```
Lead Data → Framework → Lender API
├── Validate data
├── Apply transformations
├── Make API call
├── Handle response
└── Log results
```

## 🛠️ **Technical Stack**

### **Backend**
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Primary database with async SQLAlchemy
- **Redis**: Caching and session management
- **Celery**: Background task processing
- **Pydantic**: Data validation and serialization

### **Frontend**
- **React**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Query**: Server state management
- **React Hook Form**: Form handling

### **Integration Engine**
- **Dynamic API Client**: Generates API calls based on mapping
- **Transformation Engine**: Handles data format conversions
- **Template System**: Reusable mapping configurations
- **Monitoring**: Real-time integration tracking

## 🚀 **Quick Start**

### **Prerequisites**
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### **1. Clone and Setup**
```bash
git clone <repository-url>
cd lead_integration_framework
chmod +x start.sh
chmod +x reset-docker-compose.sh
```

### **2. Start the Framework**
```bash
./start.sh
```

### **3. Access the Application**
- **Backoffice UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 **Usage Guide**

### **1. Adding a Lender**
1. Navigate to "Lenders" in the backoffice
2. Click "Add Lender"
3. Fill in lender details:
   - Name and description
   - API endpoints (POST URLs)
   - Authentication (API keys, bearer tokens)
   - Rate limits and timeouts

### **2. Configuring Field Mappings**
1. Go to "Field Mappings"
2. Use the visual mapper to:
   - Drag your fields to lender fields
   - Configure transformations
   - Set validation rules
   - Test the mapping

### **3. Testing Integrations**
1. Navigate to "Test Integrations"
2. Use sample data to test:
   - Field mapping accuracy
   - Data transformations
   - API call success
   - Error handling

### **4. Monitoring**
1. Check "Integration Dashboard"
2. Monitor:
   - API call success rates
   - Response times
   - Error logs
   - Rate limit usage

## 🔧 **Field Mapping Examples**

### **Simple Field Mapping**
```json
{
  "source_field": "full_name",
  "target_field": "customer_name",
  "transformation": "none"
}
```

### **Complex Object Mapping**
```json
{
  "source_field": "address",
  "target_field": "residential_address",
  "transformation": "object_mapping",
  "mapping": {
    "street": "address_line_1",
    "city": "city_name",
    "state": "state_code",
    "zip": "postal_code"
  }
}
```

### **Array Transformation**
```json
{
  "source_field": "phone_numbers",
  "target_field": "contact_numbers",
  "transformation": "array_format",
  "format": "phone_clean"
}
```

### **Conditional Mapping**
```json
{
  "source_field": "loan_type",
  "target_field": "product_category",
  "transformation": "conditional",
  "conditions": {
    "personal": "PERSONAL_LOAN",
    "business": "BUSINESS_LOAN",
    "home": "MORTGAGE"
  }
}
```

## 📊 **Monitoring & Analytics**

### **Integration Metrics**
- **Success Rate**: Percentage of successful API calls
- **Response Time**: Average API response time
- **Error Rate**: Failed API calls and reasons
- **Rate Limit Usage**: API quota utilization

### **Business Metrics**
- **Lead Conversion**: Leads sent vs. accepted
- **Lender Performance**: Success rates by lender
- **Field Mapping Accuracy**: Data transformation success
- **Integration Uptime**: System availability

## 🔒 **Security & Compliance**

### **Data Protection**
- **Encrypted storage** of API keys and sensitive data
- **Audit logging** of all field mapping changes
- **Access control** for backoffice users
- **Data validation** at multiple levels

### **API Security**
- **Rate limiting** to prevent abuse
- **Request signing** for sensitive APIs
- **Error handling** without exposing sensitive data
- **Secure credential management**

## 🎯 **Use Cases**

### **Loan Lead Generation**
- **Personal Loans**: Map borrower details to lender requirements
- **Business Loans**: Transform business data for different lenders
- **Mortgage**: Handle complex property and income data
- **Auto Loans**: Vehicle and financial information mapping

### **Insurance Lead Generation**
- **Life Insurance**: Health and financial data transformation
- **Auto Insurance**: Vehicle and driver information
- **Health Insurance**: Medical and personal data mapping
- **Property Insurance**: Property and risk assessment data

## 🚀 **Script Usage Examples**

### **Database Credential Setup**

The framework now includes interactive database credential prompting for enhanced security and flexibility.

#### **Interactive Mode (Recommended)**
```bash
# Run the startup script
./start.sh

# The script will prompt for:
# Enter PostgreSQL username (default: postgres): myuser
# Enter PostgreSQL password: ********
# Confirm PostgreSQL password: ********
```

#### **Environment Variable Mode**
```bash
# Set credentials via environment variables
export DB_USERNAME=myuser
export DB_PASSWORD=mypass

# Run the startup script
./start.sh

# The script will automatically use the environment variables
```

#### **Reset to Original Configuration**
```bash
# If you need to reset docker-compose.yml to original state
./reset-docker-compose.sh

# This will restore the original docker-compose.yml file
# Useful for starting over with different credentials
```

### **Practical Usage Scenarios**

#### **Scenario 1: First-Time Setup**
```bash
# 1. Clone the repository
git clone <repository-url>
cd lead_integration_framework

# 2. Make scripts executable
chmod +x start.sh reset-docker-compose.sh

# 3. Start with interactive credential setup
./start.sh

# 4. Follow the prompts to enter database credentials
# 5. Wait for services to start up
# 6. Access the application at http://localhost:3000
```

#### **Scenario 2: Production Deployment**
```bash
# 1. Set production credentials via environment variables
export DB_USERNAME=prod_user
export DB_PASSWORD=secure_prod_password

# 2. Start the framework
./start.sh

# 3. The script will use production credentials automatically
# 4. All services will be configured with production database settings
```

#### **Scenario 3: Credential Change**
```bash
# 1. Stop the current services
docker-compose down

# 2. Reset to original configuration
./reset-docker-compose.sh

# 3. Start with new credentials
./start.sh

# 4. Enter new database credentials when prompted
```

#### **Scenario 4: Development Team Setup**
```bash
# 1. Each developer can have their own credentials
./start.sh

# 2. Enter developer-specific credentials:
# Username: dev_user_1
# Password: dev_password_1

# 3. The script will update all necessary files
# 4. Services start with developer-specific configuration
```

### **Script Output Examples**

#### **Successful Startup**
```bash
🚀 Starting Lender API Integration Framework...

[INFO] Database Configuration Setup
==================================
Enter PostgreSQL username (default: postgres): myuser
Enter PostgreSQL password: ********
Confirm PostgreSQL password: ********
[SUCCESS] Database credentials set successfully!

[INFO] Updating docker-compose.yml with database credentials...
[SUCCESS] docker-compose.yml updated successfully!

[INFO] Creating necessary directories...
[INFO] Building and starting services...
[SUCCESS] PostgreSQL is ready
[SUCCESS] Redis is ready
[SUCCESS] Backend API is ready
[SUCCESS] Frontend is ready

🎉 Lender API Integration Framework is now running!

📋 Service URLs:
   • Frontend:     http://localhost:3000
   • Backend API:  http://localhost:8000
   • API Docs:     http://localhost:8000/docs
   • Health Check: http://localhost:8000/health
   • Flower:       http://localhost:5555

🗄️  Database:
   • PostgreSQL:   localhost:5432
   • Username:     myuser
   • Database:     lender_framework
   • Redis:        localhost:6379
```

#### **Error Handling**
```bash
[ERROR] Passwords do not match. Please try again.
# Script exits and allows you to run again

[ERROR] PostgreSQL is not ready
# Script exits and you can check logs with: docker-compose logs postgres
```

### **Troubleshooting Common Issues**

#### **Database Connection Issues**
```bash
# Check if PostgreSQL container is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Check database connectivity
docker-compose exec postgres pg_isready -U your_username
```

#### **Credential Reset Issues**
```bash
# If reset script fails, manually restore
cp docker-compose.yml.backup docker-compose.yml

# Or start fresh
git checkout docker-compose.yml
```

#### **Service Startup Issues**
```bash
# Check all service statuses
docker-compose ps

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend

# Restart specific service
docker-compose restart backend
```

## 🔮 **Future Enhancements**

- [ ] **AI-powered field mapping** suggestions
- [ ] **Advanced conditional logic** builder
- [ ] **Real-time integration monitoring** dashboard
- [ ] **Automated testing** framework
- [ ] **Multi-language support** for international lenders
- [ ] **Advanced analytics** and reporting
- [ ] **Webhook support** for real-time updates
- [ ] **Bulk data processing** capabilities
- [ ] **Database credential encryption** for enhanced security
- [ ] **Multi-environment configuration** support

---

**Built for seamless lead generation integrations** 🚀
