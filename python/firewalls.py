import paramiko
import subprocess
import time
import socket
import sys
import threading
import getpass
import re
from math import floor
import queue
from timeit import default_timer
from multiprocessing.dummy import Process
import os
import shutil
import glob

#Cette "class" permet de creer un objet "my_shell "qui va permettre de realiser la connexion et d'envoyer les commandes de maniere simplifiee. On retourne True quand il y a une erreur et False quand c'est ok
class my_shell:
    #Le constructeur qui initialise nos variables utilisee a travers le code
    def __init__(self, device, paramiko_exception, log_file_name):
        self.ssh = paramiko.SSHClient()
        self.s = ""
        self.device = device
        self.channel = paramiko.Channel(1)
        self.package = ()
        self.paramiko_exception = paramiko_exception
        self.list_of_context = []
        self.log_file_name = log_file_name
        self.error = False

    #Le destructeur appele lorsque l'objet meurt, on ferme la connexion lorsqu'il disparait
    def __del__(self):
        self.ssh.close()

    #Methode de l'objet permettant de realiser la connexion. Si on a une erreur, on renvoit True et on met a jour la valeur du package.
    def init(self):
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(**self.device[0], allow_agent = False, look_for_keys = False, timeout=60, auth_timeout=60, banner_timeout=60)
            self.channel = self.ssh.invoke_shell()
        except self.paramiko_exception as erreur:
            self.package = str(erreur) + ": " + self.device[2] + "\n", self.log_file_name
            self.error = True
            return True
        return False

    #"Getter" pour avoir acces au package en dehors de la classe
    def get_package(self):
        return self.package

    #"Getter" pour avoir acces au package en dehors de la classe
    def get_error(self):
        return self.error

    #"Getter" pour avoir acces au package en dehors de la classe
    def get_device(self):
        return self.device

    #"Setter" pour mettre a jour la valeur du package en dehors de la classe
    def set_package(self, message, file):
        self.package = message, file

    #Methode pour attendre les infos du shell une fois que l'on a envoye le mot de passe.
    def wait_password_processing(self):
        t = default_timer()
        while True:
            if default_timer() - t >= 60:
                self.package = "The device took too much time to process password: {}\n".format(self.device[0]["hostname"]), self.log_file_name
                self.error = True
                return True
            self.get_info()
            if self.s.endswith("> ") or self.s.endswith(">") or self.s.endswith("$") or self.s.endswith("$ ") or self.s.endswith("#") or self.s.endswith("# "):
                return False

    def check_admin(self, liste_prompt):
        for end in liste_prompt:
            if self.s.endswith(end):
                return False
        self.package = "Erreur: connexion directe dans un contexte autre que \"admin\" ou \"active\" ou \"act\": {}\n".format(self.device[2]), self.log_file_name
        self.error = True
        return True

    #Methode pour recevoir les infos du shell
    def get_info(self):
        time.sleep(0.1)
        while self.channel.recv_ready():
            self.s += self.channel.recv(9999).decode("UTF-8")
            time.sleep(0.1)

    #Methode pour verifier l'output de la commande "en", on traite chaque cas. Si on ne nous demande pas de mot de passe alors c'est qu'il y a eu un probleme
    def checking(self):
        t = default_timer()
        while True:
            self.get_info()
            if self.s.endswith("Password: ") or self.s.endswith("password: ") or self.s.endswith("password:") or self.s.endswith("Password:") or self.s.endswith("#") or self.s.endswith("# "):
                return False
            elif self.s.endswith("> ") or self.s.endswith(">") or self.s.endswith("$") or self.s.endswith("$ "):
                self.package = "Can't enter enable mode, probably different OS: {} \n".format(self.device[0]["hostname"]), self.log_file_name
                self.error = True
                return True
            elif default_timer() - t >= 60:
                self.package = "Took too much time to process \"en\" command: {} \n".format(self.device[0]["hostname"]), self.log_file_name
                self.error = True
                return True

    #Methode pour envoyer une commande au shell.Si le temps d'execution est superieur a "seconde" alors c'est trop long et on renvoit une erreur
    def send_command(self, cmd, seconds):
        t = default_timer()
        try:
            self.channel.send(cmd + "\n")
        except self.paramiko_exception as error:
            self.package = str(error) + ", replace package on queue" ": " + self.device[0]["hostname"] + "\n", self.log_file_name
            self.error = True
            return True
        while True:
            if default_timer() - t >= seconds:
                self.package = "The device took too much time to process command: {}, {}\n".format(cmd, self.device[0]["hostname"]), self.log_file_name
                self.error = True
                return True
            self.get_info()
            if self.s.endswith("#") or self.s.endswith("# "):
                return False

    def show_context(self):
        t = default_timer()
        a = ""
        try:
            self.channel.send("show context\n")
        except self.paramiko_exception as error:
            self.package = str(error) + ", replace package on queue" ": " + self.device[0]["hostname"] + "\n", self.log_file_name
            self.error = True
            return True
        while True:
            if default_timer() - t >= 60:
                self.package = "The device took too much time to process command: \"show context\": {}\n".format(self.device[0]["hostname"]), self.log_file_name
                self.error = True
                return True
            while self.channel.recv_ready():
                a += self.channel.recv(9999).decode("UTF-8")
                time.sleep(0.1)
            if a != "" and a.count("\n") > 2:
                lines = a.split("\n")
                if len(lines) < 3:
                    self.package = "Length of lines < 3: {}\n".format(self.device[2]), self.log_file_name
                    self.error = True
                    return True
                self.list_of_context = [re.split('\s+', x)[1] for x in lines if ( x[0] == ' ' and x[1].isalnum())]
                return False

    def send_netcfg(self, context = "admin"):
        t = default_timer()
        try:
            self.channel.send("netcfg\n")
            self.get_info()
            while (not self.s.endswith("#") and not self.s.endswith("# ") and not self.s.endswith(">") and not self.s.endswith("> ")):
                if default_timer() - t >= 3600:
                    self.package = "The context {} on firewall {} took too much time to process command: \"netcfg\"\n".format(context, self.device[2]), self.log_file_name
                    self.error = True
                    return True
                self.channel.send("\n")
                while not self.channel.recv_ready():
                    continue
                self.get_info()
            return False
        except self.paramiko_exception as error:
            self.package = str(error) + " Context: {}, Firewall: {}".format(context, self.device[2]), self.log_file_name
            self.error = True
            return True

    #Methode pour entrer en mode "enable". On recoit l'output du shell tant que celui-ci ne se termine pas par "#" ou "# " ou "password:" ou "password: " ou "Password:" ou "Password: ".
    def send_enable(self):
        t = default_timer()
        try:
            self.channel.send("en\n")
        except self.paramiko_exception as error:
            self.package = str(error) + ", replace package on queue" ": " + self.device[0]["hostname"] + "\n", self.log_file_name
            self.error = True
            return True
        while True:
            if default_timer() - t >= 60:
                self.package = "The device took too much time to process command: \"en\", {}\n".format(self.device[0]["hostname"]), self.log_file_name
                self.error = True
                return True
            self.get_info()
            if self.s.endswith("Password: ") or self.s.endswith("password: ") or self.s.endswith("password:") or self.s.endswith("Password:") or self.s.endswith("#") or self.s.endswith("# "):
                return False

    #Methode pour entrer en mode enable. si l'output du shell ne se termine pas par "#" alors on est pas en mode enable.
    def enable(self, secret):
        try:
            if self.s[-2] != "#" and self.s[-1] != "#":
                if self.send_enable():
                    return True
                #On verifie que la commande "en" a ete traitee, on gere les differents cas.
                if self.checking():
                    return True
                #Une fois que la commande "en" a ete traitee, on envoit le mot de passe enable.
                if self.send_command(str(secret), 60):
                    return True
                #Si apres avoir entre la mot de passe notre prompt ne se termine pas par "#" alors il y a eu un probleme.
                if self.s[-2] != "#" and self.s[-1] != "#":
                    self.package = "Unable to connect to: {}, enable password not valid\n".format(self.device[0]["hostname"]), self.log_file_name
                    self.error = True
                    return True
        #Si il y a une erreur on la mets dans le "package" et on ferme la connexion.
        except self.paramiko_exception as erreur:
            self.package = str(erreur) + ": " + self.device[0]["hostname"] + "\n", self.log_file_name
            self.error = True
            return True
        #Si on est la c'est qu'on a reussi a se connecter mais on a pas encore lance de commandes donc pour l'instant on mets dans le package qu'il y a eu une erreur sur les commandes(ce sera modifie plus tard dans le code si on arrive a lancer les commandes).
        self.package = "Connected to {} but there was an error to process commands\n".format(self.device[0]["hostname"]), self.log_file_name
        return False

#Fonction pour separer la liste d'equipements en "number_of_slices" sous liste (une pour chaque thread).
def slice_my_list(devices, number_of_slices):
    my_list_of_list = []
    x = floor(len(devices) / number_of_slices)
    for i in range(number_of_slices):
        if i == number_of_slices - 1:
            my_list_of_list.append(devices[i*x:])
            break
        my_list_of_list.append(devices[i*x:(i+1)*x])
    return my_list_of_list

#Fonction pour ecrire dans le fichier (appelee par le thread ecrivain).
def printfile(console, directory_name):
    my_package = console.get_package()
    with open(my_package[1], "a") as file:
        file.write(my_package[0])
    with open(directory_name + "/logging_info", "a") as logfile:
        logfile.write("*" * 500 + "\n")
        logfile.write(console.s)

#Fonction pour mettre au travail le thread ecrivain, il recupere son travail sur la queue. On incremente la barre de chargement d'une unite lorsque l'ecrivain a ecrit un equipement dans un fichier.
def run_printer(queue, number, queue_device, log_file_name, directory_name):
    count = number
    errors = 0
    print("equipment remaining: {} errors: {}".format(count, errors), end = "", flush = True)
    while True:
        console = queue.get()
        if console.get_error() == True:
            errors += 1
        printfile(console, directory_name)
        queue.task_done()
        count -= 1
        del console
        print("\b ", end = "\r", flush = True)
        print("equipment remaining: {} errors: {}".format(count, errors), end = "", flush = True)

# Fonction qui realise la connexion.
def process(device, paramiko_exception, log_file_name):
    liste_prompt = ["admin>", "admin> ", "admin#", "admin# ", "active>", "active> ", "active#", "active# ", "act>", "act> ", "act#", "act# "]
    #On instancie un objet "console" de type my_shell, le constructeur est appele (voir plus haut)
    console = my_shell(device, paramiko_exception, log_file_name)
    #On se connecte avec notre objet et si il y a une erreur, on met le package sur la queue.
    if console.init():
        return console
    #On attends que le mot de passe soit traite
    if console.wait_password_processing():
        return console
    #On recoit les infos du shell.
    console.get_info()
    if console.check_admin(liste_prompt):
        return console
    #On se connecte en mode enable.
    if console.enable(device[1]):
        return console
    #On envoit la commande "conf t".
    if console.send_netcfg():
        return console
    if console.send_command("changeto system", 60):
        return console
    if console.show_context():
        return console
    #On envoit les commandes.
    for i in console.list_of_context:
        if console.send_command("changeto context " + i, 60):
            return console
        if console.send_netcfg(i):
            return console
    #Si on arrive ici c'est que tout a fonctionner et on peut donc mettre a jour le package pour le signifier.
    console.set_package("Save of conexts on {} was successful\n".format(console.device[2]), log_file_name)
    #Si on arrive ici c'est qu'on est connecte en mode enable on peut donc l'ecrire dans le bon fichier.
    return console

#Fonction pour produire et mettre sur la chaine (la queue) qui est appelee avec start()
def run_worker_stage_1(queue_in, queue_out, paramiko_exception, log_file_name):
    while True:
        job = queue_in.get()
        shell = process(job, paramiko_exception, log_file_name)
        queue_out.put(shell)
        queue_in.task_done()

def get_data(name):
    #Un dictionnaire = un equipement.
    dico = {}
    #On fait la resolution dns
    process = subprocess.run(["nslookup", name], stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding="utf-8")
    if process.returncode != 0:
        return True
    else:
        lines = process.stdout.split("\n")
        lines = [x for x in lines if x]
        line = lines[-1].split()

    #Stockage de l'adresse ip de chaque equipement dans un dictionnaire different. Tous les dictionnaire sont stockes dans la liste de dico "devices".
    dico["hostname"] = line[-1]
    return dico

pwd = os.getcwd()
os.chdir("/appcacti/tftpboot/Netcfg/")
directory_name = "/appcacti/tftpboot/save_conf_" + time.strftime("%m_%Y")
log_file_name = directory_name + "/netcfg_asa_" + time.strftime("%m%Y") + ".log"
if not os.path.exists(directory_name):
    os.makedirs(directory_name)

#On tronque les deux fichiers pour qu'ils soient vide avant d'etre traites
open(log_file_name, "w+").close()
open(directory_name + "/logging_info", "w+").close()

with open(log_file_name, "a") as file:
    total, used, free = shutil.disk_usage("/appcacti/tftpboot/")
    percent = used / total
    if (percent > 0.75):
        file.write("CRITICAL error, filesystem is full at " + percent + "%, please clean it, automatic save will abort now, You will have to launch it manually or to wait next save.")
        sys.exit(1)

#Mot de passe.
password = "Dinai0!!Dinai0!!"
secret = "Dinai0!!Dinai0!!"

#Nom des fichiers.
file = "/home/network/asalist"

#Exceptions a "catcher" en cas d'erreur.
paramiko_exception = (paramiko.ssh_exception.NoValidConnectionsError,paramiko.ssh_exception.BadAuthenticationType,paramiko.ssh_exception.AuthenticationException,paramiko.ssh_exception.BadHostKeyException,paramiko.ssh_exception.ChannelException,paramiko.ssh_exception.PartialAuthentication,paramiko.ssh_exception.PasswordRequiredException,paramiko.ssh_exception.ProxyCommandFailure,paramiko.ssh_exception.SSHException,socket.timeout,
socket.error,
OSError,
ValueError,
IndexError,
ConnectionError,
ConnectionResetError)

#Liste de dictionnaire avec chaque dictionnaire representant un equipement.
devices = []

#Liste des ip qui correspond a la premiere partie de chaque ligne du fichier
list_of_ip = []
#Liste des noms qui correspond a la deuxieme partie de chaque ligne du fichier
list_of_name = []

#Ouverture du fichier des equipements et stockage de chaque equipement dans une liste.
with open(file, "r") as input_file:
    list_of_switches = input_file.readlines()

list_of_switches = [x.rstrip() for x in list_of_switches]

#On ajoute a notre liste de devices les bundles. On mets les infos utiles dans chaque bundle.
for name in list_of_switches:
    bundle = []
    bundle.append(get_data(name))
    if type(bundle[0]) is bool:
        with open(log_file_name, "a") as file:
            file.write("Command nslookup failed: " + name + "\n")
        continue
    bundle[0]["password"] = password
    bundle[0]["username"] = "app_netool"
    bundle.append(secret)
    bundle.append(name)
    devices.append(bundle.copy())

#Le dictionnaire de queue qui va contenir n queue, une pour chaque thread
dictionary_of_queues_first_layer = {}

nb_of_threads = 0

number_of_slices = len(devices)

#On decoupe la liste des equipements en fonction du nombre de thread (chaque thread s'occupe d'une partie de la liste d'equipement). On lance au plus 16 threads sinon on lance autant de thread que d'equipements
if number_of_slices >= 16:
    nb_of_threads = 16
    my_list_of_lists = slice_my_list(devices, nb_of_threads)
else:
    nb_of_threads = number_of_slices
    my_list_of_lists = slice_my_list(devices, nb_of_threads)

#On remplie chaque queue du dictionnaire avec un tuple qui va contenir deux elements: l'equipement sous forme de dictionnaire et le nom de l'equipement.
for i, slice_of_devices in enumerate(my_list_of_lists):
    dictionary_of_queues_first_layer["queue_of_devices_" + str(i)] = queue.Queue()
    for device in slice_of_devices:
        dictionary_of_queues_first_layer["queue_of_devices_" + str(i)].put(device)

#On initialise la queue "out" qui va etre traitee par le thread ecrivain (il y a donc 9 queue en tout).
print_queue = queue.Queue()

#On lance le thread ecrivain
p = Process(target = run_printer, args = (print_queue, number_of_slices, dictionary_of_queues_first_layer, log_file_name, directory_name))
p.daemon = True
p.start()

#On lance les threads producteur qui font les connexions, chaque thread travaille sur une partie de la liste des equipements.
for i in range(nb_of_threads):
    t = Process(target = run_worker_stage_1, args = (dictionary_of_queues_first_layer["queue_of_devices_" + str(i)], print_queue, paramiko_exception, log_file_name))
    t.daemon = True
    t.start()

#On attends que tous les equipements soient traites (que les queues soient vides).
for i in dictionary_of_queues_first_layer.keys():
    dictionary_of_queues_first_layer[i].join()

print_queue.join()

for file in glob.glob("*.cfg"):
    shutil.move(file, directory_name + "/" + file)

print("\n", flush=True)