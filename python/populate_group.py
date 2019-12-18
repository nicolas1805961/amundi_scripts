import paramiko
import time
import subprocess
import socket
import sys
import threading
import getpass
from math import floor
import queue
from timeit import default_timer
from multiprocessing.dummy import Process

#Cette "class" permet de creer un objet "my_shell "qui va permettre de realiser la connexion et d'envoyer les commandes de maniere simplifiee. On retourne True quand il y a une erreur et False quand c'est ok
class my_shell:
    #Le constructeur qui initialise nos variables utilisee a travers le code
    def __init__(self, device, paramiko_exception):
        self.ssh = paramiko.SSHClient()
        self.s = ""
        self.device = device
        self.channel = paramiko.Channel(1)
        self.package = ()
        self.paramiko_exception = paramiko_exception
        self.do_over = False

    #Le destructeur appele lorsque l'objet meurt, on ferme la connexion lorsqu'il disparait
    def __del__(self):
        self.channel.close()
        self.ssh.close()
    #Methode de l'objet permettant de realiser la connexion. Si on a une erreur, on renvoit True et on met a jour la valeur du package.
    def init(self):
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #print("Connecting to: {}...".format(self.device[1]))
            self.ssh.connect(**self.device[0], allow_agent = False, look_for_keys = False, timeout=15, auth_timeout=15, banner_timeout=15)
            self.channel = self.ssh.invoke_shell()
        except self.paramiko_exception as erreur:
            self.package = str(erreur) + ": " + self.device[0]["hostname"] + "\n", "wrong_file"
            return True
        return False
    #"Getter" pour avoir acces au package en dehors de la classe
    def get_package(self):
        return self.package
    #"Getter" pour avoir acces au package en dehors de la classe
    def get_device(self):
        return self.device
    #"Getter" pour avoir acces au flag do over en dehors de la classe
    def get_do_over(self):
        return self.do_over
    #"Setter" pour mettre a jour la valeur du package en dehors de la classe
    def set_package(self, message, file):
        self.package = message, file
    #Methode pour attendre les infos du shell une fois que l'on a envoye le mot de passe.
    def wait_password_processing(self):
        t = default_timer()
        while True:
            if default_timer() - t >= 15:
                self.package = "The device took too much time to process password: {}\n".format(self.device[0]["hostname"]), "wrong_file"
                return True
            self.get_info()
            if self.s.endswith("> ") or self.s.endswith(">") or self.s.endswith("$") or self.s.endswith("$ ") or self.s.endswith("#") or self.s.endswith("# "):
                return False
    #Methode pour recevoir les infos du shell
    def get_info(self):
        time.sleep(0.1)
        while self.channel.recv_ready():
            self.s += self.channel.recv(4096).decode("UTF-8")
            time.sleep(0.3)
    #Methode pour verifier l'output de la commande "en", on traite chaque cas. Si on ne nous demande pas de mot de passe alors c'est qu'il y a eu un probleme
    def checking(self):
        t = default_timer()
        while True:
            self.get_info()
            if self.s.endswith("Password: ") or self.s.endswith("password: ") or self.s.endswith("password:") or self.s.endswith("Password:") or self.s.endswith("#") or self.s.endswith("# "):
                return False
            elif self.s.endswith("> ") or self.s.endswith(">") or self.s.endswith("$") or self.s.endswith("$ "):
                self.package = "Can't enter enable mode, probably different OS: {} \n".format(self.device[0]["hostname"]), "wrong_file"
                return True
            elif default_timer() - t >= 15:
                self.package = "Took too much time to process \"en\" command: {} \n".format(self.device[0]["hostname"]), "wrong_file"
                return True
    #Methode pour envoyer une commande au shell.Si le temps d'execution est superieur a "seconde" alors c'est trop long et on renvoit une erreur
    def send_command(self, cmd, seconds):
        t = default_timer()
        a = self.s
        try:
            self.channel.send(cmd + "\n")
        except self.paramiko_exception as error:
            self.package = str(error) + ", replace package on queue" ": " + self.device[0]["hostname"] + "\n", "wrong_file"
            self.do_over = True
            return True
        while True:
            if default_timer() - t >= seconds:
                self.package = "The device took too much time to process command: {}, {}\n".format(cmd, self.device[0]["hostname"]), "wrong_file"
                self.do_over = True
                return True
            self.get_info()
            if self.s != a:
                return False
    #Methode pour entrer en mode enable. si l'output du shell ne se termine pas par "#" alors on est pas en mode enable.
    def enable(self, secret):
        try:
            if self.s[-2] != "#" and self.s[-1] != "#":
                #print("Entering enable mode...")
                if self.send_command("en", 25):
                    return True
                #On verifie que la commande "en" a ete traitee, on gere les differents cas.
                if self.checking():
                    return True
                #Une fois que la commande "en" a ete traitee, on envoit le mot de passe enable.
                if self.send_command(str(secret), 25):
                    return True
                #Si apres avoir entre la mot de passe notre prompt ne se termine pas par "#" alors il y a eu un probleme.
                if self.s[-2] != "#" and self.s[-1] != "#":
                    self.package = "Unable to connect to: {}, enable password not valid\n".format(self.device[0]["hostname"]), "wrong_file"
                    return True
        #Si il y a une erreur on la mets dans le "package" et on ferme la connexion.
        except self.paramiko_exception as erreur:
            self.package = str(erreur) + ": " + self.device[0]["hostname"] + "\n", "wrong_file"
            return True
        #Si on est la c'est qu'on a reussi a se connecter mais on a pas encore lance de commandes donc pour l'instant on mets dans le package qu'il y a eu une erreur sur les commandes(ce sera modifie plus tard dans le code si on arrive a lancer les commandes).
        self.package = "Connected to {} but there was an error to process commands\n".format(self.device[0]["hostname"]), "wrong_file"
        return False

#Fonction pour ecrire dans le fichier (appelee par le thread ecrivain).
def printfile(console):
    my_package = console.get_package()
    with open(my_package[1], "a") as file:
        file.write(my_package[0])
    with open("logging_info", "a") as logfile:
        logfile.write("*" * 500 + "\n")
        logfile.write(console.s)

#Fonction pour mettre au travail le thread ecrivain, il recupere son travail sur la queue. On incremente la barre de chargement d'une unite lorsque l'ecrivain a ecrit un equipement dans un fichier.
def run_printer(queue, number, queue_device):
    print("[%s]" % (" " * number), end="", flush=True)
    sys.stdout.write("\b" * (number + 1))
    while True:
        console = queue.get()
        if console.get_do_over():
            device = console.get_device()
            put_min_queue(queue_device, device)
            queue.task_done()
            del console
            continue
        printfile(console)
        queue.task_done()
        del console
        print("#", end="", flush=True)

#En cas d'erreur, on remets le bundle sur la queue la moins remplie
def put_min_queue(queue_device, device):
    min = 1000
    min_queue = queue.Queue()
    for t in queue_device:
        n = queue_device[t].qsize()
        if n < min:
            min = n
            min_queue = queue_device[t]
    min_queue.put(device)

# Fonction qui realise la connexion.
def process(device, paramiko_exception):
    #On instancie un objet "console" de type my_shell, le constructeur est appele (voir plus haut)
    console = my_shell(device, paramiko_exception)
    #On se connecte avec notre objet et si il y a une erreur, on met le package sur la queue.
    if console.init():
        return console
    #On attends que le mot de passe soit traite
    if console.wait_password_processing():
        return console
    #On recoit les infos du shell.
    console.get_info()
    #On se connecte en mode enable.
    if console.enable(device[2]):
        return console
    #On envoit la commande "conf t".
    if console.send_command("conf t", 25):
        return console
    #On appel l'objet.
    if console.send_command("object-group network " + str(device[3]), 25):
        return console
    #On envoie la commande pour populer le groupe. Cette derniere est differente s'il s'agit d'un ajout ou d'un retrait.
    if device[4] == "a":
        if console.send_command("network-object " + str(device[1]), 25):
            return console
    else:
        if console.send_command("no network-object " + str(device[1]), 25):
            return console
    if console.send_command("wr", 25):
        return console
    #Si on arrive ici c'est que tout a fonctionner et on peut donc mettre a jour le package pour le signifier.
    console.set_package("Connected to {} and commands sent successfully\n".format(console.device[0]["hostname"]), "correct_file")
    #Si on arrive ici c'est qu'on est connecte en mode enable on peut donc l'ecrire dans le bon fichier.
    return console

#Fonction pour produire et mettre sur la chaine (la queue) qui est appelee avec start()
def run_worker_stage_1(queue_in, queue_out, paramiko_exception):
    while True:
        job = queue_in.get()
        shell = process(job, paramiko_exception)
        queue_out.put(shell)
        queue_in.task_done()

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

def get_data(ip, name):
    #Un dictionnaire = un equipement.
    dico = {}
    #On fait la resolution dns
    while True:
        process = subprocess.run(["nslookup", name], stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding="utf-8")
        if process.returncode != 0:
            print("There was an error : " + process.stderr)
            continue
        else:
            lines = process.stdout.split("\n")
            lines = [x for x in lines if x]
            line = lines[-1].split()
            break
    #Si l'adresse ip donnee est en deux partie alors c'est un subnet et on a pas besoin du "host" dans la commande.
    ip = ip.split()
    if len(ip) < 2:
        payload = "host " + ip[0]
    else:
        payload = " ".join(ip)

    #Stockage de l'adresse ip de chaque equipement dans un dictionnaire different. Tous les dictionnaire sont stockes dans la liste de dico "devices".
    dico["hostname"] = line[1]
    return [dico, payload]

ajout_ou_retrait = ""

#Nom des fichiers.
file = input("Enter the name of the file with the devices:")
#On demande le nom de l'equipement
name = input("Indiquer le nom de l'equipement auquel la connexion doit etre etablie: ")

#Liste de listes avec chaque liste representant un equipement.
devices = []

#Mot de passe.
password = getpass.getpass(prompt="Enter password:")
secret = getpass.getpass(prompt="Enter enable password:")
#Groupe a populer
group = input("Quel est le nom du groupe d'objets ?\n")
#On demande a l'utilisateur s'il s'agit d'un ajout ou d'un retrait. Tant que l'utilisateur n'a pas entre "a" (pour ajout) ou "r" (pour retrait), on redemande.
while ajout_ou_retrait is not "a" and ajout_ou_retrait is not "r":
    ajout_ou_retrait = str(input("S'agit il d'un ajout ou d'un retrait d'un ip/subnet ? (a or r)"))

#Ouverture du fichier des equipements et stockage de chaque equipement dans une liste.
with open(file, "r") as input_file:
    list_of_switches = input_file.readlines()

#On ajoute a notre liste de devices les bundles. On mets les infos utiles dans chaque bundle.
for ip in list_of_switches:
    bundle = get_data(ip, name)
    bundle[0]["password"] = password
    bundle[0]["username"] = "network"
    bundle.append(secret)
    bundle.append(group)
    bundle.append(ajout_ou_retrait)
    devices.append(bundle)

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

#On remplie chaque queue du dictionnaire avec un bundle apres les avoir initialisees
for i, slice_of_devices in enumerate(my_list_of_lists):
    dictionary_of_queues_first_layer["queue_of_devices_" + str(i)] = queue.Queue()
    for device in slice_of_devices:
        dictionary_of_queues_first_layer["queue_of_devices_" + str(i)].put(device)

#Exceptions a "catcher" en cas d'erreur.
paramiko_exception = (paramiko.ssh_exception.NoValidConnectionsError,paramiko.ssh_exception.BadAuthenticationType,paramiko.ssh_exception.AuthenticationException,paramiko.ssh_exception.BadHostKeyException,paramiko.ssh_exception.ChannelException,paramiko.ssh_exception.PartialAuthentication,paramiko.ssh_exception.PasswordRequiredException,paramiko.ssh_exception.ProxyCommandFailure,paramiko.ssh_exception.SSHException,socket.timeout,
socket.error,
OSError,
ValueError,
IndexError)

#On initialise la queue "out" qui va etre traitee par le thread ecrivain (il y a donc 9 queue en tout).
print_queue = queue.Queue()

#On tronque les deux fichiers pour qu'ils soient vide avant d'etre traites
open("correct_file", "w").close()
open("wrong_file", "w").close()
open("logging_info", "w").close()

logging_file = open("logging_info", "a")
#On lance le thread ecrivain
p = Process(target = run_printer, args = (print_queue, number_of_slices, dictionary_of_queues_first_layer))
p.daemon = True
p.start()

#On lance les threads producteur qui font les connexions, chaque thread travaille sur une partie de la liste des equipements.
for i in range(nb_of_threads):
    t = Process(target = run_worker_stage_1, args = (dictionary_of_queues_first_layer["queue_of_devices_" + str(i)], print_queue, paramiko_exception))
    t.daemon = True
    t.start()

#On attends que tous les equipements soient traites (que les queues soient vides).
for i in dictionary_of_queues_first_layer.keys():
    dictionary_of_queues_first_layer[i].join()

print_queue.join()

#On vide le buffer stdout pour que le prompt n'ecrase pas la barre de chargement.
print("")