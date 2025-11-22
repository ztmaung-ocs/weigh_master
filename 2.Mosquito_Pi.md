✅ 1. Install Mosquitto on Orange Pi


sudo apt update
sudo apt install mosquitto mosquitto-clients -y

sudo systemctl enable mosquitto
sudo systemctl start mosquitto

systemctl status mosquitto


✅ 2. Test MQTT on Orange Pi (local broker)

mosquitto_sub -t test/topic

mosquitto_pub -t test/topic -m "Hello, MQTT!"



✅ 3. Configure Mosquitto for LAN Use (allow local network)

sudo nano /etc/mosquitto/mosquitto.conf


listener 1883
allow_anonymous true

sudo systemctl restart mosquitto




mqtt://<orange_pi_ip>:1883




