#!/bin/bash
 
# Firewall Rules for Lab Router
# Currently all ip6 traffic is dropped
# -rosencrantz

# variables
WAN_NIC="eth1"
LAN_NIC="eth0"
ROSENCRANTZ="10.9.8.100"
GUILDENSTERN="10.9.8.101"
USB_RJ45_ADAPTOR="10.9.8.102"

# Flush All Tables
iptables -F
iptables -t nat -F
ip6tables -F

# Set default policies to drop everything
iptables -P INPUT DROP
iptables -P OUTPUT DROP
iptables -P FORWARD DROP
ip6tables -P INPUT DROP
ip6tables -P OUTPUT DROP
ip6tables -P FORWARD DROP

# Allow traffic on loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow in traffic on lan interface from the dhcp-reserved addresses

iptables -A INPUT -s $ROSENCRANTZ -i $LAN_NIC -j ACCEPT
iptables -A INPUT -s $GUILDENSTERN -i $LAN_NIC -j ACCEPT
iptables -A INPUT -s $USB_RJ45_ADAPTOR -i $LAN_NIC -j ACCEPT

# Allow forwarding for reserved addresses
iptables -A FORWARD -s $ROSENCRANTZ -i $LAN_NIC -j ACCEPT
iptables -A FORWARD -d $ROSENCRANTZ -o $LAN_NIC -j ACCEPT
iptables -A FORWARD -s $GUILDENSTERN -i $LAN_NIC -j ACCEPT
iptables -A FORWARD -d $GUILDENSTERN -o $LAN_NIC -j ACCEPT
iptables -A FORWARD -s $USB_RJ45_ADAPTOR -i $LAN_NIC -j ACCEPT
iptables -A FORWARD -d $USB_RJ45_ADAPTOR -o $LAN_NIC -j ACCEPT

# Allow all traffic out on LAN interface destined for reserved addresses
iptables -A OUTPUT -d $ROSENCRANTZ -o $LAN_NIC -j ACCEPT
iptables -A OUTPUT -d $GUILDENSTERN -o $LAN_NIC -j ACCEPT
iptables -A OUTPUT -d $USB_RJ45_ADAPTOR -o $LAN_NIC -j ACCEPT

# NAT rules
iptables -t nat -A POSTROUTING -s $ROSENCRANTZ -o $WAN_NIC -j MASQUERADE
iptables -t nat -A POSTROUTING -s $GUILDENSTERN -o $WAN_NIC -j MASQUERADE
iptables -t nat -A POSTROUTING -s $USB_RJ45_ADAPTOR -o $WAN_NIC -j MASQUERADE

# Allow only established traffic back in on WAN 
iptables -A OUTPUT -o $WAN_NIC -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i $WAN_NIC -m state --state ESTABLISHED,RELATED -j ACCEPT

# Display Results
iptables -L -xvn
iptables -L -t nat
