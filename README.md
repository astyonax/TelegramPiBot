# TelegramPiBot
A flexible and simple Telegram Bot to control an acces point with [hostapd](https://wireless.wiki.kernel.org/en/users/documentation/hostapd) on Raspberry Pi

_NOTE_(18.1.5): This project uses the old library for python. 

[Telegram Bots](https://core.telegram.org/bots) are programs that run on your server/AP/.., and behave like 
almost regular Telegram users.
In particular, bots  receive, process and reply to text messages, and can be programmed to reply and act in arbitrary ways!

In telegram clients, text messages beginning with a '/' are considered  *commands* and can be sent clicking on them.

This bot controls an access point running on a raspberrypi.
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
/command ? returns command help|Partial |N

The core class `Commands` can be easily customized to accept new commands. (Partial)

## Depends 
This program depends on `python-telegram-bot`

`pip install python-telegram-bot`

## Installation
The installation is a three-steps process:
* Register the bot on the BotFather (see telegram docs)
* Write the token in the config directory $HOME/.config/G3POBOT/token and your telegram id in the code 
* modify /etc/rc.local of your server to execute the bot (eg. as: `sudo python /fullpath-to-script.py`)

## Code doc

* The class `Commands` is a context manager that receives the bot instance and configuration file.
* The class behaves also as a function that process the received messages. 
* The  `*command* ?` feature is based on the functions docstrings.
* The messages are processed by the `__call__` method that forward the content to the correct command.

**This is the first version and the code is quite messy.**
Especially the part in the main.


