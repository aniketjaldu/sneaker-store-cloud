# The Sneaker Spot - Cloud-Based E-commerce Platform

## Introduction

The Sneaker Spot is a comprehensive cloud-based e-commerce platform designed for sneaker retail. Built with modern microservices architecture, it provides a scalable, secure, and user-friendly solution for both customers and administrators. The platform features a React-based frontend, multiple backend services, and a robust authentication system.

## Project Description

The Sneaker Spot is a full-stack e-commerce application that enables users to browse, purchase, and manage sneaker inventory. The platform consists of:

### Key Features

**For Customers:**
- User registration and authentication
- Product browsing with advanced filtering and search
- Shopping cart management
- Order placement and tracking
- Password reset functionality
- User profile management

**For Administrators:**
- Complete inventory management (CRUD operations)
- User management and role assignment
- Order management and status updates
- Analytics and reporting
- Brand management
- Stock management with reservation system

### Technology Stack

- **Frontend**: React.js with Tailwind CSS
- **Backend Services**: FastAPI (Python)
- **Databases**: MySQL
- **Authentication**: JWT-based Identity Provider (IDP)
- **Load Balancing**: Nginx
- **Containerization**: Docker & Docker Compose
- **Email Service**: Postfix

## Design Architecture

The project follows a microservices architecture with the following components:

### Service Details

#### Frontend Services
- **Web User Interface** (`frontend/web-user/`): React application for customer interactions
- **Admin CLI** (`frontend/cli-admin/`): Command-line interface for administrators

#### Backend Services
- **User Service** (`user-services/`): Handles user management, authentication, orders, and cart operations
- **Inventory Service** (`inventory-services/`): Manages product catalog, stock, and inventory analytics
- **IDP Service** (`idp-services/`): Identity Provider for JWT token management and authentication
- **Email Service**: Handles email notifications for password resets and order confirmations

#### BFF (Backend for Frontend) Services
- **User BFF** (`bff-user/`): Aggregates user-related services for the frontend
- **Admin BFF** (`bff-admin/`): Aggregates admin-related services for administrative functions

#### Load Balancers
- **User Load Balancer** (`nginx/user-lb.conf`): Routes user traffic to User BFF instances
- **Admin Load Balancer** (`nginx/admin-lb.conf`): Routes admin traffic to Admin BFF instances

#### Databases
- **User Database** (`db_user/`): Stores user accounts, orders, and cart data
- **Inventory Database** (`db_inventory/`): Stores product catalog, brands, and stock information

### Network Architecture

The system uses two separate networks:
- **user-network**: For customer-facing services
- **admin-network**: For administrative services

### Port Configuration

| Service | Port | Description |
|---------|------|-------------|
| User Load Balancer | 8080 | Main customer entry point |
| Admin Load Balancer | 8081 | Main admin entry point |
| User Service | 8082 | User management API |
| Inventory Service | 8083 | Inventory management API |
| IDP Service | 8084 | Authentication service |
| User BFF 1 | 9600 | User BFF instance 1 |
| User BFF 2 | 9601 | User BFF instance 2 |
| Admin BFF 1 | 9602 | Admin BFF instance 1 |
| Admin BFF 2 | 9603 | Admin BFF instance 2 |
| User Database | 3306 | User data storage |
| Inventory Database | 3307 | Inventory data storage |
| Email Service | 1587 | Email notifications |

## Detailed Instructions on How to Run Your Project

### Prerequisites

Before running the project, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Node.js** (version 16 or higher) - for frontend development
- **Python** (version 3.8 or higher) - for local development

### Step 1: Clone and Navigate to Project

```bash
git clone <repository-url>
cd sneaker-store-cloud
```

### Step 2: Build and Start All Services

The easiest way to run the entire project is using Docker Compose:

```bash
# Build all services first
docker-compose build

# Start all services
docker-compose up

# Or build and start in one command
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

This command will:
- Build all Docker images using the Docker Compose configuration
- Create and start all containers
- Set up the networks
- Initialize the databases with sample data

### Step 3: Verify Services are Running

Check that all services are running properly:

```bash
# Check container status
docker-compose ps

# Check logs for any errors
docker-compose logs
```

### Step 4: Access the Application

Once all services are running, you can access:

- **Customer Web Interface**: http://localhost:8080
- **Admin Web Interface**: http://localhost:8081
- **User Service API**: http://localhost:8082
- **Inventory Service API**: http://localhost:8083
- **IDP Service API**: http://localhost:8084



### Additional Docker Compose Commands

For more granular control over the services:

```bash
# Build specific services only
docker-compose build user-service inventory-service

# Start specific services
docker-compose up user-service inventory-service

# View logs for specific services
docker-compose logs user-service inventory-service

# Restart specific services
docker-compose restart user-service
```

### Frontend Development

For frontend development, you can run the React app locally:

```bash
# Navigate to frontend directory
cd frontend/web-user

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at http://localhost:3000 and will proxy API requests to the backend services.

### Troubleshooting

#### Common Issues

1. **Port Conflicts**: If ports are already in use, stop existing services or change port mappings in `docker-compose.yaml`

2. **Database Connection Issues**: Ensure databases are fully initialized before starting services

3. **Network Issues**: Check that Docker networks are created properly:
   ```bash
   docker network ls
   ```

4. **Service Health Checks**: Verify services are responding:
   ```bash
   curl http://localhost:8082/  # User service
   curl http://localhost:8083/  # Inventory service
   curl http://localhost:8084/  # IDP service
   ```

#### Logs and Debugging

```bash
# View logs for specific service
docker-compose logs user-service

# Follow logs in real-time
docker-compose logs -f

# Access container shell
docker exec -it user-service /bin/bash
```

### Stopping the Project

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker-compose down -v

# Remove all containers and images
docker-compose down --rmi all
```

### Development Workflow

1. **Making Changes**: Edit source files and rebuild containers
2. **Testing**: Use the provided API endpoints for testing
3. **Database Changes**: Update SQL scripts in `db_user/` and `db_inventory/`
4. **Adding Services**: Follow the existing pattern in `docker-compose.yaml`

This comprehensive setup provides a fully functional e-commerce platform with proper separation of concerns, scalability, and maintainability.
