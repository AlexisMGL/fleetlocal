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


## Planificateur de taches Windows

<details>
<summary><strong>Configurer un lancement automatique</strong></summary>

> [!TIP]
> Utilisez pythonw.exe pour eviter qu'une fenetre de console ne s'affiche a chaque ouverture de session.

1. Ouvrir le Planificateur de taches Windows et choisir **Creer une tache...**.
2. Dans l'onglet **Declencheurs**, ajouter le declencheur **A l'ouverture d'une session**.
3. Dans l'onglet **Actions**, creer une action **Demarrer un programme** :
   - Programme/script : `C:\Chemin\vers\pythonw.exe`
   - Arguments : `c:/Chemin/vers/fleetshare_ws.py`
4. Dans l'onglet **Conditions**, decocher **Demarrer uniquement si l'ordinateur est branche sur le secteur**.
5. Enregistrer la tache puis utiliser **Executer** pour tester immediatement le streamer.

- [ ] Mettre a jour le chemin de `pythonw.exe` si Python est installe ailleurs.
- [ ] Verifier que le script s'execute sans erreur apres la connexion.

</details>
