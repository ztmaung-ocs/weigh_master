passwd

Z@w.5432!

nano /etc/ssh/sshd_config

PermitRootLogin yes
PasswordAuthentication yes


systemctl restart ssh


sudo nano /etc/ssh/sshd_config.d/50-cloud-init.conf

PasswordAuthentication yes



sudo ss -tulwn

sudo ufw allow 22/tcp
sudo ufw allow 17113/tcp
sudo ufw allow 54692/tcp

sudo ufw enable
sudo ufw status





