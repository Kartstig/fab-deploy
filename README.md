# Fabric Deploy

## Installation

### Ubuntu
```
$ sudo apt-get install python python-pip fabric
```

## Running Fabric
#### Install your favorite debian VM
#### Set up APT proxies in /etc/apt/apt.conf
```
Acquire::http::Proxy "http:://myproxy:myport";
Acquire::https::Proxy "http:://myproxy:myport";
Acquire::ftp::Proxy "http:://myproxy:myport";
```
#### Install openssh-server
```
sudo apt-get install openssh-server
```
#### Target your VM in the hosts file 
```
env.host = [ <user>@ip.ad.re.ss ]
```
#### Run Fabric!
```
fab deploy
```
