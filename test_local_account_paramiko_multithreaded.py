import paramiko
from getpass import getpass
import logging
import time
import socket
import sys
from threading import Thread, Timer
from math import floor
import queue

#Fonction qui se declenche si un thread reste bloque dans une boucle.
def warning():
    print("password processing time too long")

# Fonction pour attendre que le mot de passe s'affiche sur la console interactive.
def wait_password_processing(channel):
    s = ""
    t = Timer(15.0, warning)
    t.start()
    while True:
        while channel.recv_ready():
            s += channel.recv(4096).decode("UTF-8")
            time.sleep(0.3)
        if s != "":
            t.cancel()
            t.join()
            return s
        if not t.is_alive():
            return "123"

# Fonction pour attendre que la commande "en" soit traite, on traite chaque cas.
def checking(channel):
    s = ""
    t = Timer(15.0, warning)
    t.start()
    while True:
        while channel.recv_ready():
            s += channel.recv(4096).decode("UTF-8")
            time.sleep(0.3)
        if s.endswith("Password: ") or s.endswith("password: ") or s.endswith("password:") or s.endswith("Password:") or s.endswith("#") or s.endswith("# "):
            t.cancel()
            t.join()
            return 0
        elif s.endswith("> ") or s.endswith(">") or s.endswith("$") or s.endswith("$ "):
            t.cancel()
            t.join()
            return 1
        if not t.is_alive():
            return 2

#Fonction pour separer la liste d'equipements en 8 sous liste (une pour chaque thread).
def slice_my_list(devices):
    my_list_of_list = []
    x = floor(len(devices) / 8)
    for i in range(8):
        if i == 7:
            my_list_of_list.append(devices[i*x:])
            break
        my_list_of_list.append(devices[i*x:(i+1)*x])
    return my_list_of_list

#Classe pour le thread consommateur (le thread qui se contente d'ecrire dans les fichiers) qui prends les informations a ecrire sur la queue.
class print_thread(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def printfile(self, message, filename):
        with open(filename, "a") as file:
            file.write(message)

    def run(self):
        while True:
            my_tuple = self.queue.get()
            self.printfile(*my_tuple)
            self.queue.task_done()

#Classe pour les threads producteur (realisent la connexion et mettent les informations a ecrire dans la queue).
class process_thread(Thread):
    def __init__(self, paramiko_exception, queue_in, queue_out):
        Thread.__init__(self)
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.my_paramiko_exception = paramiko_exception

    # Fonction qui realise la connexion.
    def process(self, device):
        # s va recevoir les infos du shell.
        s = ""
        # Formalites pour initier la connexion
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #Bloc try/catch(except) pour "catcher" les erreurs.
        try:
            #Connection sur l'équipement device parmis la liste de "devices".
            print("Connecting to: {}...".format(device["hostname"]))
            ssh.connect(**device, allow_agent = False, look_for_keys = False, timeout=10, auth_timeout=15, banner_timeout=15)
            #On invoque le shell interractif
            channel = ssh.invoke_shell()
            #On attends que le mot de passe soit traite.
            s += wait_password_processing(channel)
            if s.endswith("123"):
                return "The device took too much time to process password: {}\n".format(device["hostname"]), "wrong_file"
            #Si le shell a des infos à nous envoyer on les récupèrent.
            while channel.recv_ready():
                s += channel.recv(4096).decode("UTF-8")
                time.sleep(0.3)
            while True:
                #On sort de la boucle de communication si on a traité toutes les commandes (on incrémente nb à chaque commande traitée, voir plus bas).
                """if nb == len(list_of_commands):
                    break"""
                #Si le shell a des infos à nous envoyer on les récupèrent.
                while channel.recv_ready():
                    s += channel.recv(4096).decode("UTF-8")
                    time.sleep(0.3)
                    #Si ce que nous a envoyé le shell ne se termine pas par "#" alors nous ne somme pas en mode enable et donc on passe en mode enable en envoyant "en" puis le mot de passe enable (secret). Une fois qu'on est en enable on repart au debut de la boucle pour recevoir ce qu'affiche le shell.
                if s[-2] != "#" and s[-1] != "#":
                    print("Entering enable mode...")
                    channel.send("en\n")
                    #On verifie que la commande "en" a ete traitee, on gere les differents cas.
                    x = checking(channel)
                    if x == 1:
                        return "Can't enter enable mode, probably different OS: {} \n".format(device["hostname"]), "wrong_file"
                    elif x == 2:
                        return "The device took too much time to process \"en\" command: {}\n".format(device["hostname"]), "wrong_file"
                    #Une fois que la commande "en" a ete traitee, on envoit le mot de passe enable.
                    channel.send(str(secret) + "\n")
                    #On attends que le mot de passe soit traite.
                    s += wait_password_processing(channel)
                    if s.endswith("123"):
                        return "The device took too much time to process password: {}\n".format(device["hostname"]), "wrong_file"
                    #Si apres avoir entre la mot de passe notre prompt ne se termine pas par "#" alors il y a eu un probleme.
                    if s[-2] != "#" and s[-1] != "#":
                        return "Unable to connect to: {}, enable password not valid\n".format(device["hostname"]), "wrong_file"
                    continue
                #Si on arrive ici c'est qu'on est connecté en mode enable on peut donc l'écrire dans le bon fichier.
                print("Connected to {}".format(device["hostname"]))
                return "Connected to {}\n".format(device["hostname"]), "correct_file"

                """correct_file.write("Connected to {}\n".format(device["hostname"]))
                print("Connected to {}".format(device["hostname"]))
                break"""
                """channel.send(list_of_commands[nb] + "\n")
                time.sleep(4)
                nb += 1"""
        #On "catche" les exceptions en cas d'erreur et on les écrits dans le fichier des erreurs.
        except self.my_paramiko_exception as e:
            return str(e) + ": " + device["hostname"] + "\n", "wrong_file"
    #Fonction pour produire et mettre sur la chaine (la queue) qui est appelee avec start()
    def run(self):
        while True:
            job = self.queue_in.get()
            my_tuple = self.process(job)
            self.queue_out.put(my_tuple)
            self.queue_in.task_done()

#Mot de passe simple et mot de passe enable.
password = "OmS&H1N1!"
secret = "Dinai0!!"

#Exceptions à "catcher" en cas d'erreur.
paramiko_exception = (paramiko.ssh_exception.NoValidConnectionsError,paramiko.ssh_exception.BadAuthenticationType,paramiko.ssh_exception.AuthenticationException,paramiko.ssh_exception.BadHostKeyException,paramiko.ssh_exception.ChannelException,paramiko.ssh_exception.PartialAuthentication,paramiko.ssh_exception.PasswordRequiredException,paramiko.ssh_exception.ProxyCommandFailure,paramiko.ssh_exception.SSHException,socket.timeout,
ValueError,
IndexError)

#Liste de dictionnaire avec chaque dictionnaire représentant un équipement.
devices = []

#Un dictionnaire = un équipement.
dico = {}

#Info à recevoir du shell intractif.
s = ""

#Liste des ip qui correspond a la premiere partie de chaque ligne du fichier
list_of_ip = []

#Initialisation du logging qui sera écrit dans le fichier "logging_info".
logging.basicConfig(filename = "logging_info", filemode = "w", format = "[%(levelname)s]: %(asctime)s %(message)s", level = logging.INFO)

#Ouverture du fichier des équipements et stockage de chaque équipement dans une liste.
with open("/home/network/host.txt", "r") as input_file:
    list_of_switches = input_file.readlines()

#On enleve la premiere ligne du fichier qui ne nous interesse pas
del(list_of_switches[0])

#On recupere la premiere partie de chaque ligne du fichier (les adresses ip)
for i in list_of_switches:
    temp_list = i.split()
    list_of_ip.append(temp_list[0])

#Ouverture du fichier des commandes et stockage dans une liste.
"""with open("", "r") as input_commands:
    list_of_commands = input_commands.readlines()"""

#Variable initialisé à 0 et qui sera incrémentée à chaque commande traitée de manière à passser à l'équipement suivant lorsque nb = nombre de commandes.
nb = 0

#Stockage de l'adresse ip de chaque équipement dans un dictionnaire différent. Tous les dictionnaire sont stockés dans la liste de dico "devices".
for switch in list_of_ip:
    dico["hostname"] = switch
    dico["username"] = "network"
    dico["password"] = password
    devices.append(dico.copy())

#Le dictionnaire de queue qui va contenir 8 queue, une pour chaque thread
dictionary_of_queues = {}

list_of_threads = []

#On decoupe la liste des equipements en 8
my_list_of_lists = slice_my_list(devices)

#On remplie chaque queue du dictionnaire
for i, slice_of_devices in enumerate(my_list_of_lists):
    dictionary_of_queues["queue_of_devices_" + str(i)] = queue.Queue()
    for device in slice_of_devices:
        dictionary_of_queues["queue_of_devices_" + str(i)].put(device)

#On initialise la queue "out" qui va etre traitee par le thread ecrivain (il y a donc 9 queue en tout).
print_queue = queue.Queue()

#On tronque les deux fichiers pour qu'ils soient vide avant d'etre traites
open("correct_file", "w").close()
open("wrong_file", "w").close()

#On lance le thread ecrivain
pt = print_thread(print_queue)
pt.setDaemon(True)
pt.start()

#On lance les threads producteur qui font les connexions, chaque thread travaille sur une partie de la liste des equipements.
for i in range(8):
    t = process_thread(paramiko_exception, dictionary_of_queues["queue_of_devices_" + str(i)], print_queue)
    t.setDaemon(True)
    list_of_threads.append(t)
    t.start()

#On attends que tous les equipements soient traites (que les queues soient vides).
for i in dictionary_of_queues.keys():
    dictionary_of_queues[i].join()

"""for i in list_of_threads:
    i.join()

pt.join()"""
