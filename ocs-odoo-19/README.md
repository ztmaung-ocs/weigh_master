# ocs-odoo-fleet
 Fleet Management System 1.0


# Build the custom image for the 'web' service
docker-compose build web

# Start all services in detached mode
docker-compose up -d


docker compose exec --user root web sh

apt update && apt install -y nano htop

pip install --break-system-packages paho-mqtt



# create odoo module (for print directly to printer)

docker compose exec web odoo scaffold print_directly_to_printer /mnt/extra-addons/myaddons

update12