# TelegramPiBot
A flexible and simple Telegram Bot to control an acces point with hostapd on raspberrypi

Telegram Bots [https://core.telegram.org/bots] are a simple way to 
send commands and receive status updates to your telegram client (ideally, android & co).

This bot allows to control an access point running on a raspberrypi.
At the moment, the bot can:

Feature | Status | Admin
----------| ------------ |------
Shutdown  | Yes| Y
Reboot | Yes|Y
List connected clients | Partial (via arp -a)|N
Show SSID and PW| Yes |N
Admin/no admin user| Yes| --
Show help|Y|N
List commands|Y|N
Report errors to admin|Y|--

The core class `Commands` can be easily customized to accept new commands. (Partial)

## Depends 
This program depends on `python-telegram-bot`

`pip install python-telegram-bot`

## Installation
The installation is a three-steps process:
* Register the bot on the BotFather (see telegram docs)
* Write the token in the config directory $HOME/.config/G3POBOT/token and your telegram id in the code 
* modify /etc/rc.local of your server to execute the bot (eg. as: `sudo python /fullpath-to-script.py`)

