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
Acquire::http::Proxy "http:://proxy.jpmchase.net:8443";
Acquire::https::Proxy "http:://proxy.jpmchase.net:8443";
Acquire::ftp::Proxy "http:://proxy.jpmchase.net:8443";
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
