# Fleet Local

Ce dépôt contient le script `fleetshare_ws.py` permettant d'envoyer les données MAVLink vers mon serveur FleetShare 🚀.

## Prérequis 📦

- Python 3.8 ou supérieur installé sur votre machine. Vous pouvez le télécharger sur [python.org](https://www.python.org/downloads/).
- Une connexion Internet pour installer les dépendances Python.

## Installation et exécution sous Windows PowerShell 💻

1. Ouvrez **Windows PowerShell**.
2. Positionnez-vous dans le répertoire du projet :
   ```powershell
   cd chemin\vers\le\dossier\cloné
   ```
3. (Optionnel) Créez un environnement virtuel pour isoler les dépendances :
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```
4. Installez les dépendances définies dans `requirements.txt` :
   ```powershell
   pip install -r requirements.txt
   ```
5. Lancez le script depuis un terminal 🖥️:
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

