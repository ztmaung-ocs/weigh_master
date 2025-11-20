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










