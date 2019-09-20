import paramiko
from getpass import getpass
import logging
import time

#Mot de passe simple et mot de passe enable.
password = "OmS&H1N1!"
secret = "Dinai0!!"

#Exceptions à "catcher" en cas d'erreur.
paramiko_exception = (paramiko.ssh_exception.NoValidConnectionsError,
                    ValueError)

#Liste de dictionnaire avec chaque dictionnaire représentant un équipement.
devices = []

#Un dictionnaire = un équipement.
dico = {}

#Info à recevoir du shell intractif.
s = ""

#Initialisation du logging qui sera écrit dans le fichier "logging_info".
logging.basicConfig(filename = "logging_info", filemode = "w", format = "[%(levelname)s]: %(asctime)s %(message)s", level = logging.INFO)

#Ouverture du fichier des équipements et stockage de chaque équipement dans une liste.
with open("file", "r") as input_file:
    list_of_switches = input_file.readlines()

#Ouverture du fichier des commandes et stockage dans une liste.
"""with open("", "r") as input_commands:
    list_of_commands = input_commands.readlines()"""

#Variable initialisé à 0 et qui sera incrémentée à chaque commande traitée de manière à passser à l'équipement suivant lorsque nb = nombre de commandes.
nb = 0

#Stockage de l'adresse ip de chaque équipement dans un dictionnaire différent. Tous les dictionnaire sont stockés dans la liste de dico "devices".
for switch in list_of_switches:
    dico["hostname"] = switch
    devices.append(dico.copy())
#Ouverture du bon et du mauvais fichier.
with open("correct_file", "w") as correct_file, open("wrong_file", "w") as wrong_file:
    #On itére sur chaque équipement et pour chaque équipement(dictionnaire) on ajoute le username et le password. Avant on avait juste l'adresse ip dans chaque dico cf ligne 32.
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for device in devices:
        device["username"] = "network"
        device["password"] = password
        #Bloc try/catch(except) pour "catcher" les erreurs.
        try:
            #Connection sur l'équipement device parmis la liste de "devices".
            print(device)
            ssh.connect(**device, allow_agent = False, look_for_keys = False, auth_timeout=5, banner_timeout=5)
            #On invoque le shell interractif
            channel = ssh.invoke_shell()
            #Boucle pour communiquer avec le shell de manière indéfinie, on traite chaque cas:
            while True:
                #On sort de la boucle de communication si on a traité toutes les commandes (on incrémente nb à chaque commande traitée, voir plus bas).
                """if nb == len(list_of_commands):
                    break"""
                #Si le shell a des infos à nous envoyer on les récupèrent. Si on les a récupérés alors le code saute au prochain "if"(on ne tombe pas dans le "else").
                if channel.recv_ready():
                    s += channel.recv(4096).decode("UTF-8")
                    #Sinon on repart au début de la boucle où l'on demandera à nouveau au shell si il a des infos.
                else:
                    continue
                #Si ce que nous a envoyé le shell ne se termine pas par "#" alors nous ne somme pas en mode enable et donc on passe en mode enable en envoyant "en" puis le mot de passe enable (secret). Une fois qu'on est en enable on repart au debut de la boucle pour recevoir ce qu'affiche le shell.
                if not s.endswith("#"):
                    channel.send("en\n")
                    channel.send(str(secret) + "\n")
                    time.sleep(0.5)
                    continue
                #Si on arrive ici c'est qu'on est connecté en mode enable on peut donc l'écrire dans le bon fichier.
                correct_file.write("Connected to {}".format(device["hostname"]))
                break
                """channel.send(list_of_commands[nb] + "\n")"""
                time.sleep(4)
                nb += 1
        #On "catche" les exceptions en cas d'erreur et on les écrits dans le fichier des erreurs.
        except paramiko_exception as e:
            wrong_file.write(str(e.errors))
ssh.close()