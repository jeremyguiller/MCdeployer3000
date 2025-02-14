# MCDeployer3000

MCDeployer3000 est une API Python pour déployer et gérer des serveurs Minecraft à l'aide de conteneurs Docker. L'API permet de créer, lister, arrêter, redémarrer et supprimer des serveurs Minecraft en utilisant l'image Docker `itzg/minecraft-server`.

## Fonctionnalités

- **Créer un serveur Minecraft** : Déployez un serveur Minecraft avec des options personnalisables (version, mods, mémoire, etc.).
- **Lister les serveurs** : Affichez la liste des serveurs Minecraft en cours d'exécution ou arrêtés.
- **Arrêter un serveur** : Arrêtez un serveur Minecraft spécifique.
- **Redémarrer un serveur** : Redémarrez un serveur Minecraft spécifique.
- **Supprimer un serveur** : Supprimez un serveur Minecraft spécifique.

## Prérequis

- **Docker** : Assurez-vous que Docker est installé et en cours d'exécution sur votre machine.
- **Python 3.10** : Le projet utilise Python 3.10.
- **Dépendances** : Installez les dépendances nécessaires avec `uv`.

## Installation

1. Clonez le dépôt :

   ```bash
   git clone https://github.com/votre-utilisateur/MCDeployer3000.git
   cd MCDeployer3000
   ```

2. sync les dépendances avec `uv` :

   ```bash
   uv sync
   ```

3. Lancez l'API :

   ```bash
   uvicorn api:app --reload
   ```

   L'API sera disponible à l'adresse `http://127.0.0.1:8000`.

## Utilisation

### Créer un serveur

Envoyez une requête POST à `/create-server/` avec les paramètres suivants :

```bash
curl -X POST "http://127.0.0.1:8000/create-server/" -H "Content-Type: application/json" -d '{
  "server_name": "mon_serveur",
  "version": "latest",
  "port": 25565,
  "eula": "true",
  "type": "PAPER",
  "memory": "2G"
}'
```

### Lister les serveurs

Envoyez une requête GET à `/list-servers/` :

```bash
curl -X GET "http://127.0.0.1:8000/list-servers/"
```

### Arrêter un serveur

Envoyez une requête POST à `/stop-server/{server_name}` :

```bash
curl -X POST "http://127.0.0.1:8000/stop-server/mon_serveur"
```

### Redémarrer un serveur

Envoyez une requête POST à `/restart-server/{server_name}` :

```bash
curl -X POST "http://127.0.0.1:8000/restart-server/mon_serveur"
```

### Supprimer un serveur

Envoyez une requête POST à `/delete-server/{server_name}` :

```bash
curl -X POST "http://127.0.0.1:8000/delete-server/mon_serveur"
```

## Tests

Pour exécuter les tests, utilisez `pytest` :

```bash
pytest test_unittest.py -v
```




