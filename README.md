# GhostPurge-Linux : Documentation Utilisateur (Debian 13)

## 1. Prérequis GhostPurge-Linux
Avant d'installer GhostPurge, assurez-vous que votre système respecte les critères suivants :
- **Version minimale** : Debian 13 (Trixie) ou distribution basée sur Debian.
- **Droits nécessaires** : Accès `sudo` (privilèges administrateur) requis pour l'installation du service `systemd` et la surveillance des répertoires systèmes.
- **Paquets requis** : Python 3.11 ou supérieur, `pip`, et `systemd`.
- **Répertoires surveillés** : GhostPurge nécessite l'accès en lecture à `/var/log/`, `/var/lib/dpkg/`, `/etc/`, ainsi qu'aux répertoires locaux de l'utilisateur (`~/.config/`, `~/.local/share/`, `~/.cache/`).
- **Ports et permissions** : Aucun port réseau n'est utilisé. GhostPurge s'exécute strictement en local.

## 2. Installation GhostPurge-Linux

L'installation de GhostPurge se fait de manière isolée dans le répertoire `/opt/` pour garantir la stabilité de votre système Debian.

### Étape 1 : Déploiement des fichiers
Ouvrez votre terminal et exécutez les commandes suivantes pour copier le projet dans `/opt/` :
```bash
sudo cp -r . /opt/ghostpurge
cd /opt/ghostpurge
```

### Étape 2 : Création de l'environnement Python
Sur Debian 13, il est recommandé de créer un environnement virtuel (`venv`) pour isoler les dépendances Python :
```bash
sudo rm -rf venv
sudo apt update && sudo apt install python3-venv python3-pip -y
sudo python3 -m venv venv
```

### Étape 3 : Installation des dépendances et modules (Watchers & Cleaners)
Installez les modules internes de GhostPurge via `pip` :
```bash
sudo /opt/ghostpurge/venv/bin/pip install -e .
```

### Étape 4 : Installation du service systemd
Le service `systemd` permet à GhostPurge de tourner silencieusement en arrière-plan.
```bash
sudo cp /opt/ghostpurge/systemd/ghostpurge.service /etc/systemd/system/
```

### Étape 5 : Activation du service
Rechargez le démon systemd et activez GhostPurge pour qu'il démarre à chaque lancement du système :
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ghostpurge
```

## 3. Configuration GhostPurge-Linux
Le comportement de GhostPurge est entièrement personnalisable grâce au fichier `ghostpurge.yaml`.

### Emplacement et permissions
Exécutez ces commandes pour initialiser la configuration :
```bash
sudo mkdir -p /etc/ghostpurge
sudo cp conf/config.yaml.template /etc/ghostpurge/config.yaml
sudo nano /etc/ghostpurge/config.yaml
```
*Note : Seul l'utilisateur `root` doit avoir les droits d'écriture sur ce fichier.*

### Contenu du fichier ghostpurge.yaml
- **Modes de nettoyage** :
  - `conservateur` : Ne supprime que les fichiers officiellement déclarés et stricts.
  - `agressif` : Mode par défaut. Supprime les configurations, caches et dépendances orphelines.
  - `hyper-agressif` : Traque et supprime toute trace portant le nom du paquet (Attention : risques de faux positifs).
- **Liste blanche (whitelist)** : Permet de définir des dossiers ou applications intouchables (ex: `mozilla`, `ssh`).
- **Liste noire (blacklist)** : Oblige GhostPurge à toujours nettoyer ces éléments, indépendamment des règles heuristiques.
- **Configuration des Watchers** : Permet d'activer (`true`) ou de désactiver (`false`) individuellement la surveillance de certains gestionnaires de paquets (ex: `watcher_steam: false`).
- **Configuration des Cleaners** : Permet de désactiver certaines phases de nettoyage (ex: `clean_systemd: false` pour ne pas toucher aux services locaux).

N'oubliez pas d'éditer le fichier pour remplacer `/home/user` par le chemin absolu vers votre propre dossier personnel.

## 4. Exécution GhostPurge-Linux
GhostPurge est un service d'arrière-plan. Il n'a pas d'interface graphique.

### Démarrage et Vérification
Pour démarrer le service manuellement :
```bash
sudo systemctl start ghostpurge
```

Pour vérifier qu'il est en cours d'exécution sans erreur :
```bash
sudo systemctl status ghostpurge
```
*Le statut affiché doit être `active (running)`.*

### Redémarrage automatique et fonctionnement silencieux
En cas de crash de `inotify` ou d'une erreur inattendue, le service est configuré (`Restart=always`) pour redémarrer automatiquement. Il consomme moins de 1% de processeur et n'émet aucune notification de bureau.

### Emplacement des logs
Les opérations sont enregistrées dans :
`/var/log/ghostpurge.log`

## 5. Surveillance GhostPurge-Linux (Les Watchers)
GhostPurge détecte les désinstallations en temps réel grâce à une batterie de capteurs (Watchers).

1. **Watcher dpkg / apt**
   - **Ce qu'il surveille** : Les fichiers `/var/log/dpkg.log` et `/var/lib/dpkg/status` via `inotify`.
   - **Comment il détecte** : Il repère les lignes d'état indiquant `remove` ou `purge`.
   - **Déclenchement** : Il transmet le nom exact du paquet aux Cleaners.

2. **Watcher flatpak**
   - **Ce qu'il surveille** : `/var/lib/flatpak/exports/share/applications` et `~/.local/share/flatpak`.
   - **Comment il détecte** : Il écoute les modifications de l'arborescence OSTree liées aux désinstallations.

3. **Watcher snap**
   - **Ce qu'il surveille** : Les montages système dans `/snap/`.
   - **Comment il détecte** : Il intercepte le démontage (unmount) d'une image squashfs d'une application Snap.

4. **Watcher AppImage**
   - **Ce qu'il surveille** : Vos dossiers locaux typiques (ex: `~/.local/bin` ou le dossier `Applications`).
   - **Comment il détecte** : Il utilise `inotify` pour repérer la suppression physique d'un fichier `.AppImage`.

5. **Watcher Steam**
   - **Ce qu'il surveille** : `~/.local/share/Steam/steamapps/common/`.
   - **Comment il détecte** : La disparition d'un sous-dossier de jeu déclenche le nettoyage des prefixes Proton (compatdata).

6. **Watcher pip (Python)**
   - **Ce qu'il surveille** : `/usr/local/lib/python3.*/dist-packages` et `~/.local/lib/`.
   - **Comment il détecte** : Suppression des dossiers `.dist-info` ou `.egg-info`.

7. **Watcher npm (NodeJS)**
   - **Ce qu'il surveille** : Le répertoire global `/usr/local/lib/node_modules/` et `~/.npm`.
   - **Comment il détecte** : Suppression des dossiers de modules globaux.

8. **Watcher filesystem (Dossiers Orphelins)**
   - **Ce qu'il surveille** : Vos dossiers `%HOME%`.
   - **Comment il détecte** : Si vous supprimez manuellement le dossier source d'une application compilée, GhostPurge nettoie les fichiers `.config` liés.

## 6. Nettoyage GhostPurge-Linux (Les Cleaners)
Une fois une désinstallation détectée, GhostPurge lance ses nettoyeurs (Cleaners) en séquence :

1. **Suppression des dossiers orphelins** : GhostPurge recherche dans `~/.local/share/` et supprime les bases de données ou médias résiduels de l'application.
2. **Suppression des fichiers de configuration résiduels** : Il scrute `~/.config/` et `/etc/` pour supprimer les fichiers `.conf`, `.ini`, ou `.xml` qui portent le nom du paquet.
3. **Suppression des caches** : Il vide les dossiers relatifs au paquet situés dans `~/.cache/`, libérant ainsi un espace disque conséquent.
4. **Suppression des logs** : Il nettoie les journaux applicatifs dans `/var/log/` et `~/.local/state/`.
5. **Suppression des services systemd obsolètes** : Il supprime les fichiers `.service` ou `.timer` dans `~/.config/systemd/user/` créés par l'application et lance un `systemctl --user daemon-reload`.
6. **Suppression des dépendances orphelines** : Si un paquet est désinstallé, GhostPurge appelle `apt autoremove --purge -y` silencieusement.
7. **Suppression des paquets en état rc** : Il nettoie les résidus Dpkg des anciennes installations en lançant `dpkg -P $(dpkg -l | awk '/^rc/ { print $2 }')`.

## 7. Vérification du bon fonctionnement

- **Tester les Watchers** : Installez un paquet léger (ex: `htop` via `sudo apt install htop`), puis désinstallez-le (`sudo apt remove htop`).
- **Lire les logs** : Ouvrez un terminal et tapez :
  ```bash
  tail -f /var/log/ghostpurge.log
  ```
  Vous devriez voir `[dpkg] Détection de la suppression de htop` suivi des étapes de nettoyage.
- **Simuler une désinstallation** : GhostPurge inclut un mode dry-run. Vous pouvez forcer un événement en lançant :
  ```bash
  sudo /opt/ghostpurge/venv/bin/python main.py --simulate htop
  ```

## 8. Dépannage / Troubleshooting

### Le service systemd ne démarre pas
- **Cause** : Le chemin d'accès vers Python dans `ghostpurge.service` est incorrect ou le script est cassé.
- **Solution** : Vérifiez le fichier `/etc/systemd/system/ghostpurge.service`. Assurez-vous que l'`ExecStart` pointe bien vers `/opt/ghostpurge/venv/bin/python`.
- **Commande de vérification** : `sudo journalctl -u ghostpurge -n 50`

### Permissions manquantes
- **Cause** : Le service n'est pas lancé en tant que `root`.
- **Solution** : Dans le fichier `ghostpurge.service`, la ligne `User=` doit être absente ou définie sur `root`.
- **Commande de vérification** : `ps aux | grep ghostpurge`

### Watchers inactifs ou événements ratés
- **Cause** : Le fichier `/var/log/dpkg.log` n'est pas lisible ou le quota `inotify` du kernel est épuisé.
- **Solution** : Augmentez la limite inotify via sysctl.
- **Commande de vérification** : `sysctl fs.inotify.max_user_watches`

### Logs absents
- **Cause** : Le dossier `/var/log/` ne permet pas à GhostPurge d'y écrire.
- **Solution** : Vérifiez l'espace disque (`df -h`) et créez le fichier manuellement avec `sudo touch /var/log/ghostpurge.log && sudo chmod 644 /var/log/ghostpurge.log`.

### Erreurs Python
- **Cause** : Une dépendance (`pyyaml`, etc.) est manquante.
- **Solution** : Réinstallez les dépendances (`sudo /opt/ghostpurge/venv/bin/pip install -e .`).

### Erreurs liées à un paquet précis (Flatpak, Snap, Pip)
- **Cause** : Le chemin binaire de `flatpak`, `snap`, ou `pip` n'est pas dans le PATH du service root.
- **Solution** : Spécifiez les chemins absolus (ex: `/usr/bin/flatpak`) dans le fichier `/etc/ghostpurge/config.yaml`.

## 9. FAQ GhostPurge-Linux

**GhostPurge supprime-t-il trop de fichiers ?**
Non. Par défaut, GhostPurge fonctionne en mode "agressif" mais intelligent. Il applique une vérification croisée (anti-update) pour ne pas supprimer vos données si vous êtes simplement en train de mettre à jour un paquet.

**Comment ajouter un dossier à la liste blanche ?**
Ouvrez `/etc/ghostpurge/config.yaml`, trouvez la section `whitelist` et ajoutez le nom exact du dossier ou de l'application (ex: `- "steam"`). GhostPurge ignorera toute action liée à ce terme.

**Comment désactiver un watcher précis ?**
Dans le même fichier `config.yaml`, passez la valeur du watcher de `true` à `false` (ex: `watcher_npm: false`). Relancez ensuite le service (`sudo systemctl restart ghostpurge`).

**Comment activer le mode hyper-agressif ?**
Changez la valeur de `mode:` dans `config.yaml` de `agressif` à `hyper-agressif`. Redémarrez le service. *Attention : utilisez ce mode uniquement si vous maîtrisez parfaitement votre système.*

**Comment vérifier que GhostPurge ne supprime pas un logiciel installé ?**
GhostPurge croise toujours l'information de désinstallation avec la base de données du système (ex: `dpkg-query`). S'il reçoit un événement inotify de suppression mais que l'application est toujours marquée comme installée, il annule le nettoyage.

**Comment mettre à jour GhostPurge ?**
1. Allez dans le répertoire : `cd /opt/ghostpurge`
2. Tirez la dernière version Git : `sudo git pull`
3. Redémarrez le service : `sudo systemctl restart ghostpurge`
