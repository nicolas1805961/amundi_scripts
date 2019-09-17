import os
import subprocess
import string
import sys

my_file = input("name of the file to read from: ")

with open(my_file, "r") as file:
    my_list = file.readlines()

with open("ip_file", "w") as file1:
    for name in my_list:
        name = name.rstrip("\n")
        result = subprocess.run(["host", name], stdout = subprocess.PIPE)
        result = result.stdout.decode("UTF-8").split(" ")
        file1.write(result[-1])