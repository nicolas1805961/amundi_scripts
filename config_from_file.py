import netmiko
import paramiko
from getpass import getpass
import os
import logging
import sys

password = "OmS&H1N1!" #getpass("Enter password: ")
secret = "Dinai0!!" #getpass("Enter enable password: ")

netmiko_exception = (paramiko.ssh_exception.NoValidConnectionsError,                                netmiko.ssh_exception.NetMikoTimeoutException,                                  netmiko.ssh_exception.NetMikoAuthenticationException,
                    ValueError)
devices = []
dico = {}

logging.basicConfig(format = "[%(levelname)s]: %(asctime)s %(message)s", level = logging.INFO)

with open("correct_file", "r") as input_file:
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
        device["session_log"] = "dmz1_output.txt"
        device["global_delay_factor"] = 4
        #device["blocking_timeout"] = 16
        try:
            guesser = netmiko.SSHDetect(**device)
            best_match = guesser.autodetect()
            if best_match is None:
                wrong_file.write("Error {}: can not find device type\n".format(device["ip"]))
                continue
            else:
                device["device_type"] = best_match
            connect = netmiko.ConnectHandler(**device)
            prompt = connect.find_prompt()
            if not prompt.endswith("#"):
                connect.enable()
            output = connect.send_config_from_file("")
            print(output)
        except netmiko_exception as e:
            wrong_file.write(e)
        else:
            correct_file.write(device["ip"])
            connect.disconnect()