import paramiko
import time
import socket
import sys
import threading
import getpass
from math import floor
import queue
from timeit import default_timer
from multiprocessing.dummy import Process

#Cette "class" permet de créer un objet "my_shell "qui va permettre de réaliser la connexion et d'envoyer les commandes de manière simplifiee. On retourne True quand il y a une erreur et False quand c'est ok
class my_shell:
    #Le constructeur qui initialise nos variables utilisee a travers le code
    def __init__(self, device, paramiko_exception, secret):
        self.secret = secret
        self.ssh = paramiko.SSHClient()
        self.s = ""
        self.device = device
        self.channel = paramiko.Channel(1)
        self.package = ()
        self.paramiko_exception = paramiko_exception
        self.has_error = False
    #Le destructeur appele lorsque l'objet meurt, on ferme la connexion lorsqu'il disparait
    def __del__(self):
        self.ssh.close()
    #Methode de l'objet permettant de realiser la connexion. Si on a une erreur, on renvoit True et on met a jour la valeur du package.
    def init(self):
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #print("Connecting to: {}...".format(self.device[1]))
            self.ssh.connect(**self.device[0], allow_agent = False, look_for_keys = False, timeout=10, auth_timeout=15, banner_timeout=15)
            self.channel = self.ssh.invoke_shell()
        except self.paramiko_exception as erreur:
            self.ssh.close()
            self.package = str(erreur) + ": " + self.device[1] + "\n", "wrong_file"
            self.has_error = True
            return True
        return False
    #"Getter" pour avoir acces au package en dehors de la classe
    def get_package(self):
        return self.package
    #"Getter" pour avoir acces au flag d'erreur en dehors de la classe
    def get_flag_error(self):
        return self.has_error
    #"Setter" pour mettre a jour la valeur du package en dehors de la classe
    def set_package(self, message, file):
        self.package = message, file
    #Methode pour attendre les infos du shell une fois que l'on a envoye le mot de passe.
    def wait_password_processing(self):
        a = self.s
        t = default_timer()
        while True:
            if default_timer() - t >= 15:
                self.ssh.close()
                self.package = "The device took too much time to process password: {}\n".format(self.device[1]), "wrong_file"
                self.has_error = True
                return True
            self.get_info()
            if self.s != a:
                return False
    #Methode pour recevoir les infos du shell
    def get_info(self):
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
                self.ssh.close()
                self.package = "Can't enter enable mode, probably different OS: {} \n".format(self.device[1]), "wrong_file"
                self.has_error = True
                return True
            elif default_timer() - t >= 15:
                self.ssh.close()
                self.package = "Took too much time to process \"en\" command: {} \n".format(self.device[1]), "wrong_file"
                self.has_error = True
                return True
    #Methode pour envoyer une commande au shell.Si le temps d'execution est superieur a "seconde" alors c'est trop long et on renvoit une erreur
    def send_command(self, cmd, seconds):
        a = self.s
        self.channel.send(cmd + "\n")
        t = default_timer()
        while True:
            if default_timer() - t >= seconds:
                self.ssh.close()
                self.package = "The device took too much time to process command: {}, {}\n".format(cmd, self.device[1]), "wrong_file"
                self.has_error = True
                return True
            self.get_info()
            if self.s != a:
                return False
    #Methode pour entrer en mode enable. si l'output du shell ne se termine pas par "#" alors on est pas en mode enable.
    def enable(self):
        try:
            if self.s[-2] != "#" and self.s[-1] != "#":
                #print("Entering enable mode...")
                if self.send_command("en", 15):
                    return True
                #On verifie que la commande "en" a ete traitee, on gere les differents cas.
                if self.checking():
                    return True
                #Une fois que la commande "en" a ete traitee, on envoit le mot de passe enable.
                if self.send_command(str(self.secret), 15):
                    return True
                #Si apres avoir entre la mot de passe notre prompt ne se termine pas par "#" alors il y a eu un probleme.
                if self.s[-2] != "#" and self.s[-1] != "#":
                    self.ssh.close()
                    self.package = "Unable to connect to: {}, enable password not valid\n".format(self.device[1]), "wrong_file"
                    self.has_error = True
                    return True
        #Si il y a une erreur on la mets dans le "package" et on ferme la connexion.
        except self.paramiko_exception as erreur:
            self.ssh.close()
            self.package = str(erreur) + ": " + self.device[1] + "\n", "wrong_file"
            self.has_error = True
            return True
        #Si on est la c'est qu'on a reussi a se connecter mais on a pas encore lance de commandes donc pour l'instant on mets dans le package qu'il y a eu une erreur sur les commandes(ce sera modifie plus tard dans le code si on arrive a lancer les commandes).
        self.package = "Connected to {} but there was an error to process commands\n".format(self.device[1]), "wrong_file"
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
def printfile(console):
    my_package = console.get_package()
    with open(my_package[1], "a") as file:
        file.write(my_package[0])
    with open("logging_info", "a") as logfile:
        logfile.write(console.s)

#Fonction pour mettre au travail le thread ecrivain, il recupere son travail sur la queue. On incrémente la barre de chargement d'une unité lorsque l'ecrivain a écrit un équipement dans un fichier.
def run_printer(queue, number):
    print("[%s]" % (" " * number), end="", flush=True)
    #sys.stdout.write("[%s]" % (" " * number))
    #sys.stdout.flush()
    sys.stdout.write("\b" * (number + 1))
    while True:
        console = queue.get()
        printfile(console)
        queue.task_done()
        print("#", end="", flush=True)
        #print("")
        #sys.stdout.write("#")
        #sys.stdout.flush()

# Fonction qui realise la connexion.
def process_stage_1(device, paramiko_exception, secret):
    #On instancie un objet "console" de type my_shell, le constructeur est appele (voir plus haut)
    console = my_shell(device, paramiko_exception, secret)
    #On se connecte avec notre objet et si il y a une erreur, on met le package sur la queue.
    if console.init():
        return console
    #On attends que le mot de passe soit traite
    if console.wait_password_processing():
        return console
    #On recoit les infos du shell.
    console.get_info()
    #On se connecte en mode enable.
    if console.enable():
        return console
    #Si on arrive ici c'est qu'on est connecté en mode enable on peut donc l'écrire dans le bon fichier.
    #print("Connected to {}".format(device[1]))
    return console


def process_stage_2(commands, console):
    if console.get_flag_error():
        return console
    #On envoit la commande "conf t".
    if console.send_command("conf t", 15):
        return console
    #On envoit les commandes.
    #print("Sending commands")
    for i in commands:
        if console.send_command(i, 15):
            return console
    #Si on arrive ici c'est que tout a fonctionner et on peut donc mettre a jour le package pour le signifier.
    console.set_package("Connected to {} and commands sent successfully\n".format(console.device[1]), "correct_file")
    #print("commands sent")
    #Le package est place sur la queue et sera traite par le thread ecrivain.
    return console

#Fonction pour produire et mettre sur la chaine (la queue) qui est appelee avec start()
def run_worker_stage_1(queue_in, queue_out, paramiko_exception, secret):
    while True:
        job = queue_in.get()
        shell = process_stage_1(job, paramiko_exception, secret)
        queue_out.put(shell)
        queue_in.task_done()

#Fonction pour produire et mettre sur la chaine (la queue) qui est appelee avec start()
def run_worker_stage_2(queue_in, queue_out, commands):
    while True:
        shell = queue_in.get()
        my_package = process_stage_2(commands, shell)
        queue_out.put(my_package)
        queue_in.task_done()

#Mot de passe.
password = getpass.getpass(prompt="Enter password:")
secret = getpass.getpass(prompt="Enter enable password:")
#Nom des fichiers.
file = input("Enter the name of the file with the devices:")
cmds = input("Enter the name of the file with the commands:")

#Exceptions à "catcher" en cas d'erreur.
paramiko_exception = (paramiko.ssh_exception.NoValidConnectionsError,paramiko.ssh_exception.BadAuthenticationType,paramiko.ssh_exception.AuthenticationException,paramiko.ssh_exception.BadHostKeyException,paramiko.ssh_exception.ChannelException,paramiko.ssh_exception.PartialAuthentication,paramiko.ssh_exception.PasswordRequiredException,paramiko.ssh_exception.ProxyCommandFailure,paramiko.ssh_exception.SSHException,socket.timeout,
socket.error,
ValueError,
IndexError)

#Liste de dictionnaire avec chaque dictionnaire représentant un équipement.
devices = []

#Un dictionnaire = un équipement.
dico = {}

#Liste des ip qui correspond a la premiere partie de chaque ligne du fichier
list_of_ip = []
#Liste des noms qui correspond a la deuxième partie de chaque ligne du fichier
list_of_name = []

#Ouverture du fichier des équipements et stockage de chaque équipement dans une liste.
with open(file, "r") as input_file:
    list_of_switches = input_file.readlines()

#On enleve la premiere ligne du fichier qui ne nous interesse pas
#del(list_of_switches[0])

#On recupere la premiere et la seconde partie de chaque ligne du fichier (les adresses ip). Si c'est un firewall on ne l'ajoute pas aux listes.
for i in list_of_switches:
    temp_list = i.split()
    if "fw" in temp_list[1].lower() or "rb" in temp_list[1].lower():
        continue
    list_of_ip.append(temp_list[0])
    list_of_name.append(temp_list[1])

#Ouverture du fichier des commandes et stockage dans une liste.
with open(cmds, "r") as input_commands:
    list_of_commands = input_commands.readlines()
list_of_commands = [x for x in list_of_commands if x != "\n" and x != ""]

#Stockage de l'adresse ip de chaque équipement dans un dictionnaire différent. Tous les dictionnaire sont stockés dans la liste de dico "devices".
for switch in list_of_ip:
    dico["hostname"] = switch
    dico["username"] = "network"
    dico["password"] = password
    devices.append(dico.copy())

#Le dictionnaire de queue qui va contenir n queue, une pour chaque thread
dictionary_of_queues_first_layer = {}
dictionary_of_queues_second_layer = {}

nb_of_threads = 0

number_of_slices = len(list_of_ip)
#On decoupe la liste des equipements en fonction du nombre de thread (chaque thread s'occupe d'une partie de la liste d'equipement). On lance au plus 16 threads sinon on lance autant de thread que d'equipements
if number_of_slices >= 16:
    nb_of_threads = 16
    my_list_of_lists = slice_my_list(devices, nb_of_threads)
    list_of_list_of_name = slice_my_list(list_of_name, nb_of_threads)
else:
    nb_of_threads = number_of_slices
    my_list_of_lists = slice_my_list(devices, nb_of_threads)
    list_of_list_of_name = slice_my_list(list_of_name, nb_of_threads)

#On remplie chaque queue du dictionnaire avec un tuple qui va contenir deux elements: l'equipement sous forme de dictionnaire et le nom de l'equipement. C'est la partie la plus complexe du code. On itère sur 2 liste simultanément avec zip.
for i, slice_of_devices in enumerate(my_list_of_lists):
    dictionary_of_queues_first_layer["queue_of_devices_" + str(i)] = queue.Queue()
    dictionary_of_queues_second_layer["queue_of_objects_" + str(i)] = queue.Queue()
    for device, name in zip(slice_of_devices, list_of_list_of_name[i]):
        dictionary_of_queues_first_layer["queue_of_devices_" + str(i)].put((device, name))

#On initialise la queue "out" qui va etre traitee par le thread ecrivain (il y a donc 9 queue en tout).
print_queue = queue.Queue()

#On tronque les deux fichiers pour qu'ils soient vide avant d'etre traites
open("correct_file", "w").close()
open("wrong_file", "w").close()
open("logging_info", "w").close()

logging_file = open("logging_info", "a")
#On lance le thread ecrivain
p = Process(target = run_printer, args = (print_queue, number_of_slices))
p.daemon = True
p.start()

#On lance les threads producteur qui font les connexions, chaque thread travaille sur une partie de la liste des equipements.
for i in range(nb_of_threads):
    t = Process(target = run_worker_stage_1, args = (dictionary_of_queues_first_layer["queue_of_devices_" + str(i)], dictionary_of_queues_second_layer["queue_of_objects_" + str(i)], paramiko_exception, secret))
    l = Process(target = run_worker_stage_2, args = (dictionary_of_queues_second_layer["queue_of_objects_" + str(i)], print_queue, list_of_commands))
    t.daemon = True
    l.daemon = True
    t.start()
    l.start()

#On attends que tous les equipements soient traites (que les queues soient vides).
for i, j in zip(dictionary_of_queues_first_layer.keys(), dictionary_of_queues_second_layer.keys()):
    dictionary_of_queues_first_layer[i].join()
    dictionary_of_queues_second_layer[j].join()

print_queue.join()

#On vide le buffer stdout pour que le prompt n'écrase pas la barre de chargement.
print("")