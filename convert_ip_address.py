import os
import subprocess
import string

my_file = input("name of the file to read from: ")

with open(my_file, "r") as file:
    my_list = file.readlines()

with open("ip_file", "w") as file:
    for name in my_list:
        result = subprocess.run(["host", name], stdout = subprocess.PIPE)
        result = result.stdout.decode("UTF-8").split(" ")
        file.write(result[-1] + "\n")