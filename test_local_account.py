import netmiko
from getpass import getpass
import os
import logging
import sys

password = "OmS&H1N1!" #getpass("Enter password: ")
secret = "Dinai0!!" #getpass("Enter enable password: ")

netmiko_exception = (netmiko.ssh_exception.NetMikoTimeoutException,                                    netmiko.ssh_exception.NetMikoAuthenticationException)
devices = []
dico = {}

logging.basicConfig(format = "%(asctime)s %(message)s")
logger = logging.getLogger()

with open("file", "r") as input_file:
    list_of_switches = input_file.readlines()

for switch in list_of_switches:
    dico["ip"] = switch
    devices.append(dico.copy())

with open("correct_file", "w") as correct_file, open("wrong_file", "w") as wrong_file:
    for device in devices:
        device["password"] = password
        device["username"] = "network"
        device["secret"] = secret
        device["device_type"] = "autodetect"

        guesser = netmiko.SSHDetect(**device)

        print(device)
        sys.exit(0)

        best_match = guesser.autodetect()
        if best_match is None:
            print("Error {}: can not find device type\n".format(device["host"]))
            continue
        else:
            device["device_type"] = best_match

        device["global_delay_factor"] = 6
        logger.info("connecting to {}\n".format(device["ip"]))
        try:
            connect = netmiko.ConnectHandler(**device)
            connect.enable()
        except netmiko_exception as e:
            wrong_file.write("Failed connexion to: {} {}\n".format(device["ip"], e))
        else:
            correct_file.write("Connected to: \n", device["ip"])
        connect.disconnect()
logger.info("finished\n")