# Telegram-server-panel
Bot for controlling servers, remote executing commands. <br/>
Official [app](https://github.com/Mootfrost777/Admin-panel-server-API/settings) to run on server

#config/default.json
```
{
  "db": {
    "name": <db name>,
    "host": <db ip>,
    "port": <db port>,
    "user": <db user>,
    "password": <db password>
  },
  "bot": {
    "token": "<bot token>
  },
  "page": {
    "per_page": <elements per page, 10 recommended>
  },
  "run_command": <URL template for running command, to use with official API use: "http://{ip}:{port}/run_command?">
}
```
