# Fleet Local

Ce dépôt contient le script `fleetshare_ws.py` permettant d'envoyer les données MAVLink vers mon serveur FleetShare 🚀.

## Télécharger le projet 📥

Deux méthodes permettent de récupérer ce dépôt :

- **Cloner avec Git**
  ```bash
  git clone https://github.com/AlexisMGL/fleetlocal.git
  ```
- **Télécharger l'archive ZIP depuis GitHub**
  Sur la page du dépôt, cliquez sur **Code** puis **Download ZIP**, puis décompressez l'archive.

## Prérequis 📦

- Python 3.8 ou supérieur installé sur votre machine. Vous pouvez le télécharger sur [python.org](https://www.python.org/downloads/).
- Une connexion Internet pour installer les dépendances Python.

## Installation et exécution sous Windows PowerShell 💻

1. Ouvrez **Windows PowerShell**.
2. Positionnez-vous dans le répertoire du projet :
   ```powershell
   cd chemin\vers\le\dossier\cloné
   ```
3. Installez les dépendances définies dans `requirements.txt` :
   ```powershell
   pip install -r requirements.txt
   ```
4. Lancez le script depuis un terminal 🖥️:
   ```powershell
   python fleetshare_ws.py
   ```

Le script se connecte au flux MAVLink fourni par `WS_URI` et envoie périodiquement les données au serveur HTTP configuré.

## Messages d'erreur ⚠️

En cas de message d'erreur ou de blocage du script, tentez les étapes suivantes :

1. Appuyez sur **CTRL+W** pour tuer le script dans la console. 🛑
2. Utilisez la **flèche du haut** pour rappeler la commande précédente. ⬆️
3. Appuyez sur **Entrée** pour relancer le script. 🔁

Si les erreurs persistent, vérifiez votre connexion Internet et les paramètres `WS_URI` et `HTTP_ENDPOINT`.

## Utilisation en vol ✈️

Le streamer doit rester **lancé pendant tout le vol** afin de continuer d'envoyer
les informations télémétriques. Ces informations sont disponibles sous forme
de données brutes sur
<https://fleetshare.onrender.com/drone-position> et peuvent être visualisées
sur la carte à l'adresse <https://fleetshare.onrender.com>.

Si le streamer est connecté lorsque le pilote envoie la commande « Lecture PN »,
il récupère alors les *waypoints* de la mission et les affiche également sur
l'interface web.




## Execution automatique avec le Planificateur de taches Windows

1. Ouvre `taskschd.msc` et cree une **Nouvelle tache** (par exemple "FleetShare WS").
2. Onglet **Actions** :
   - `Programme/script` -> `C:\Users\alexi\AppData\Local\Programs\Python\Python313\pythonw.exe` (ou ta version de Python).
   - `Ajouter des arguments` -> `C:\Users\alexi\Desktop\AlexisMGL\fleetlocal\fleetshare_ws.py`.
   - `Demarrer dans` -> `C:\Users\alexi\Desktop\AlexisMGL\fleetlocal`.
3. Onglet **Declencheurs** :
   - Ajoute "A l'ouverture de session" ou "Au demarrage" selon le besoin.
   - Active "Recommencer toutes les 5 minutes" si tu veux qu'il se relance apres un arret.
4. Onglet **Conditions** :
   - Decoche "Demarrer la tache uniquement si l'ordinateur est sur secteur" pour l'executer sur batterie.
5. Onglet **Parametres** :
   - Coche "Autoriser l'execution a la demande" et laisse "Arreter la tache si elle s'execute plus de" desactive.
6. Valide la tache puis clique sur **Executer** pour tester :
   - La fenetre console n'apparait pas grace a `pythonw.exe`.
   - Le script attend automatiquement que `MissionPlanner.exe` ou `GCSAM.exe` soit lance avant de commencer a envoyer les donnees, et se remet en attente si tu fermes ces programmes.

