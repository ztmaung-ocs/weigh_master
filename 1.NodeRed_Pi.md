user : root
password : orangepi


apt-get update
apt-get install -y build-essential curl git

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm install 14 --source
nvm use 14
node -v
npm -v

npm install -g --unsafe-perm node-red@3.1.9
node-red


Server now running at http://127.0.0.1:1880/
http://<orange_pi_ip>:1880








 nvm which 14
/root/.nvm/versions/node/v14.21.3/bin/node

nano /etc/systemd/system/node-red.service

[Unit]
Description=Node-RED
After=network.target

[Service]
# Run as root (your current setup)
User=root
Group=root

# Point to your nvm node + node-red
Environment="NODE_OPTIONS="
Environment="NODE_RED_HOME=/root/.node-red"
Environment="NVM_DIR=/root/.nvm"
ExecStart=/root/.nvm/versions/node/v14.21.3/bin/node /root/.nvm/versions/node/v14.21.3/lib/node_modules/node-red/red.js --userDir /root/.node-red

# Restart on crash
Restart=on-failure
KillSignal=SIGINT
Type=simple

[Install]
WantedBy=multi-user.target





systemctl daemon-reload
systemctl enable node-red
systemctl start node-red
systemctl status node-red

journalctl -u node-red -f

journalctl -u node-red -n 100 --no-pager


ls -l /dev/ttyUSB*
    crw-rw---- 1 root dialout 188, 0 Nov 21 02:24 /dev/ttyUSB0

sudo chmod a+rw /dev/ttyUSB0


cd ~/.node-red

npm install node-red-node-serialport@1.0.4

npm install node-red-dashboard


systemctl restart node-red
