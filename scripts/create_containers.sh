docker build -t user-bff:latest ../bff-user
docker build -t admin-bff:latest ../bff-admin
docker build -t inventory-service:latest ../inventory-services
docker build -t user-service:latest ../user-services
docker build -t idp-service:latest ../idp-services