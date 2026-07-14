# GhostPurge-Windows : Documentation Utilisateur

## 1. Introduction
GhostPurge-Windows est un utilitaire de nettoyage intelligent fonctionnant en arrière-plan sous Windows 10 et Windows 11. Il surveille silencieusement votre système et détecte chaque désinstallation d'application. Dès qu'une désinstallation est repérée, GhostPurge nettoie automatiquement les fichiers de configuration résiduels, les dossiers locaux et autres traces (fichiers orphelins) généralement oubliées par les installeurs classiques. Le but est de préserver les performances de votre ordinateur et de libérer de l'espace disque de manière totalement transparente.

## 2. Prérequis
Pour installer et utiliser GhostPurge-Windows, votre système doit réunir les conditions suivantes :
- **Système d'exploitation** : Windows 10 ou Windows 11 (64-bits recommandé).
- **Droits d'accès** : Privilèges Administrateur requis (pour l'installation du service et l'accès au registre système).
- **Réseau** : Connexion internet requise uniquement lors de la phase d'installation pour le téléchargement des prérequis (Python).

## 3. Installation

### Étape 1 : Installation de Python
GhostPurge nécessite Python 3.11 ou une version supérieure.
1. Téléchargez la dernière version de Python depuis le site officiel : https://www.python.org/downloads/windows/
2. Exécutez l'installeur.
3. **⚠️ Avertissement crucial** : Cochez impérativement la case **"Add python.exe to PATH"** située en bas de la toute première fenêtre de l'installeur avant de cliquer sur *Install Now*.

### Étape 2 : Installation des dépendances
Ouvrez une invite de commande **PowerShell en tant qu'Administrateur** (Clic droit sur le menu Démarrer > Windows PowerShell (admin) ou Terminal (admin)) et exécutez les commandes suivantes :

```powershell
# Mise à jour du gestionnaire de paquets pip
python -m pip install --upgrade pip

# Installation des bibliothèques nécessaires à GhostPurge
pip install psutil pywin32 wmi pyyaml
```

### Étape 3 : Configuration du module système (pywin32)
La bibliothèque logicielle permettant à Python d'interagir avec les services Windows nécessite une étape d'enregistrement spécifique. Toujours dans votre console Administrateur, lancez cette commande d'une ligne qui automatise la configuration :

```powershell
python -c "import sys; import os; os.system(sys.executable + ' ' + os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pywin32_postinstall.py') + ' -install')"
```

### Étape 4 : Installation du service Windows GhostPurge
Placez le dossier contenant les fichiers de GhostPurge (par exemple `C:\GhostPurge`) à un emplacement permanent sur votre disque où il ne sera pas effacé.
Dans votre PowerShell Administrateur, naviguez vers ce dossier et installez le service :

```powershell
cd C:\GhostPurge
python main_windows.py --install
```

## 4. Configuration
La configuration par défaut est conçue pour être optimale et fonctionner de manière autonome sans aucune intervention. 
Le fichier de configuration principal est créé automatiquement lors du premier lancement à cet emplacement :
`C:\ProgramData\GhostPurge\ghostpurge.yaml`

Vous pouvez l'ouvrir avec le Bloc-notes standard de Windows si vous souhaitez modifier des comportements avancés. Notez que toute modification nécessite un redémarrage du service pour être prise en compte.

## 5. Exécution

### Démarrage du service
Pour lancer GhostPurge en arrière-plan, tapez la commande suivante dans PowerShell (Admin) :
```powershell
python main_windows.py --start
```
*Astuce : Le service GhostPurge est configuré pour se lancer ensuite automatiquement à chaque redémarrage de votre ordinateur.*

### Fonctionnement silencieux en arrière-plan
GhostPurge est un véritable *Service Windows*. Il ne possède pas d'interface graphique et ne viendra pas vous déranger avec des fenêtres de confirmation ou des pop-ups. Il protège votre système silencieusement, sans jamais interrompre votre travail.

## 6. Vérification
Comment s'assurer que GhostPurge fonctionne correctement ?

### Vérification de l'état du service
Vous pouvez vérifier que GhostPurge est bien en cours d'exécution via PowerShell :
```powershell
Get-Service GhostPurge
```
Le statut (`Status`) doit afficher `Running`. 
Alternativement, vous pouvez appuyer sur `Touche Windows + R`, taper `services.msc` et chercher "GhostPurge" dans la liste des services Windows locaux.

### Vérification des watchers (capteurs d'événements)
GhostPurge s'appuie sur trois piliers pour détecter les désinstallations sans impacter vos performances :
1. **Registre Windows** : Intercepte en temps réel (via API native) la suppression d'une clé de registre liée à un programme.
2. **WMI (Windows Management Instrumentation)** : Détecte le lancement des processus liés aux désinstalleurs (ex: `uninstall.exe`).
3. **Filesystem** : Surveille les suppressions de répertoires dans `%APPDATA%`, `%LOCALAPPDATA%` et `Program Files`.

**Test grandeur nature :**
1. Installez une application légère (ex: VLC media player).
2. Ouvrez l'application une fois pour qu'elle génère son dossier de configuration dans `C:\Users\<VotreNom>\AppData\Roaming`.
3. Fermez l'application et désinstallez-la normalement (depuis les Paramètres Windows ou le Panneau de configuration).
4. Ouvrez l'explorateur de fichiers et naviguez dans votre dossier `AppData\Roaming`. Le dossier orphelin de l'application aura été automatiquement purgé par GhostPurge.

## 7. Logs (Journaux d'événements)
GhostPurge consigne minutieusement chacune de ses actions (détections et suppressions).
L'emplacement du fichier log est :
`C:\ProgramData\GhostPurge\ghostpurge.log`

Pour visualiser les derniers événements en direct via PowerShell :
```powershell
Get-Content C:\ProgramData\GhostPurge\ghostpurge.log -Tail 20 -Wait
```

Vous y verrez des entrées claires telles que :
- `[registry] Uninstalled package detected: VLC`
- `[cleaner] Removed orphaned folder: C:\Users\User\AppData\Roaming\vlc`

## 8. Dépannage / Troubleshooting

### Le service ne démarre pas
**Symptôme** : Erreur "Access Denied" ou le service s'arrête immédiatement après le démarrage.
**Solution** : Assurez-vous d'avoir exécuté `python main_windows.py --install` depuis un PowerShell exécuté **en tant qu'Administrateur**. Si l'erreur persiste, relancez l'étape 3 (Configuration du module pywin32).

### Python introuvable
**Symptôme** : Le mot 'python' n'est pas reconnu comme nom d'applet de commande.
**Solution** : Vous avez oublié de cocher "Add python.exe to PATH" lors de l'installation de Python. Relancez l'installeur Python, choisissez "Modify", puis cochez l'option en bas de la fenêtre.

### Dépendances manquantes
**Symptôme** : Le log affiche `ModuleNotFoundError: No module named 'wmi'` (ou un autre module).
**Solution** : Dans un PowerShell Admin, retapez : `pip install psutil pywin32 wmi pyyaml`.

### Logs absents ou introuvables
**Symptôme** : Le dossier `C:\ProgramData\GhostPurge` n'existe pas.
**Solution** : GhostPurge n'a probablement jamais réussi à démarrer (voir section "Le service ne démarre pas"). Lancez GhostPurge en mode console interactive pour diagnostiquer l'erreur en direct :
```powershell
cd C:\GhostPurge
python main_windows.py --console
```

### Événements non capturés (Registre inaccessible ou WMI désactivé)
**Symptôme** : Les désinstallations fonctionnent mais les dossiers AppData restent présents.
**Solution** : 
1. Le service d'infrastructure WMI de votre système Windows est peut-être désactivé. Assurez-vous que le service Windows "Infrastructure de gestion Windows" (Winmgmt) est bien en cours d'exécution dans `services.msc`.
2. Assurez-vous d'avoir laissé tourner le service pendant au moins 10 secondes, GhostPurge intègre un délai de sécurité (anti-update) avant de nettoyer.

## 9. FAQ

**GhostPurge risque-t-il de supprimer mes fichiers personnels ?**
Non. GhostPurge est conçu pour cibler exclusivement les répertoires standards de configuration applicative (`AppData` locaux et itinérants, dossiers `ProgramData`). De plus, il vérifie l'état de l'application (pour éviter les suppressions accidentelles lors d'une simple mise à jour logicielle).

**GhostPurge ralentit-il mon ordinateur (ou consomme-t-il de la batterie) ?**
Absolument pas. L'architecture native sous Windows permet à GhostPurge de "dormir" complètement au niveau du processeur (consommation CPU à 0%). Il est réveillé directement par Windows uniquement lorsqu'un événement majeur (comme une désinstallation) se produit.

**L'application fonctionne-t-elle avec des applications portables ?**
GhostPurge détecte l'activité à travers le système d'installation natif de Windows. Si une application portable n'y est pas inscrite de manière standard (aucune clé de désinstallation), elle ne déclenchera pas l'analyse automatique.
