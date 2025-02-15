import os
import shutil
import docker
import httpx
import pytest
from fastapi.testclient import TestClient
from api import app, SERVER_DATA_DIR  # Importez SERVER_DATA_DIR depuis api.py

#client = TestClient(app)
client = httpx.Client(base_url="http://localhost:8000", timeout=30.0)  # Augmentez le délai d'attente à 30 secondes


def test_create_server_basic():
    """ Test de création d'un serveur avec les paramètres de base """
    response = client.post(
        "/create-server/",
        json={
            "server_name": "test_server_basic",
            "version": "latest",
            "port": 25565,
            "eula": "true"
        }
    )
    assert response.status_code == 200
    assert "container_id" in response.json()

def test_create_server_with_mods():
    """ Test de création d'un serveur avec des mods et une whitelist """
    response = client.post(
        "/create-server/",
        json={
            "server_name": "test_server_mods",
            "version": "latest",
            "port": 25567,  # Nouveau port
            "eula": "true",
            "mods": ["mod1.jar", "mod2.jar"],
            "whitelist": "player1,player2"
        }
    )
    assert response.status_code == 200
    assert "container_id" in response.json()

def test_list_servers():
    """ Vérifie que la liste des serveurs est bien retournée """
    response = client.get("/list-servers/")
    assert response.status_code == 200
    servers = response.json()["servers"]
    assert isinstance(servers, list)
    assert any(server["name"] == "test_server_basic" for server in servers)

def test_restart_server():
    """ Test du redémarrage d'un serveur """
    response = client.post("/restart-server/test_server_basic")
    assert response.status_code == 200
    assert response.json() == {"message": "Server test_server_basic restarted successfully"}

def test_restart_nonexistent_server():
    """ Test de tentative de redémarrage d'un serveur inexistant """
    response = client.post("/restart-server/nonexistent_server")
    assert response.status_code == 404
    assert response.json() == {"detail": "Server nonexistent_server not found"}

def test_delete_server():
    """ Test de suppression d'un serveur existant """
    create_response = client.post(
        "/create-server/",
        json={
            "server_name": "test_server_to_delete",
            "version": "latest",
            "port": 25568,  # Nouveau port
            "eula": "true"
        }
    )
    assert create_response.status_code == 200

    delete_response = client.post("/delete-server/test_server_to_delete")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Server test_server_to_delete deleted successfully"}

    list_response = client.get("/list-servers/")
    assert "test_server_to_delete" not in [server["name"] for server in list_response.json()["servers"]]

def test_delete_nonexistent_server():
    """ Vérifie la suppression d'un serveur qui n'existe pas """
    response = client.post("/delete-server/nonexistent_server")
    assert response.status_code == 404
    assert response.json() == {"detail": "Server nonexistent_server not found"}

def test_check_ports():
    """ Vérifie que chaque serveur créé utilise le bon port """
    response = client.get("/list-servers/")
    servers = response.json()["servers"]

    # Vérification des ports de chaque serveur
    for server in servers:
        if server["name"] == "test_server_basic":
            assert server["port"] == 25565
        elif server["name"] == "test_server_mods":
            assert server["port"] == 25567

def test_create_server_creates_data_directory():
    """ Vérifie que le dossier local est créé dans ServerData lors de la création d'un serveur """
    server_name = "test_server_data_dir"
    response = client.post(
        "/create-server/",
        json={
            "server_name": server_name,
            "version": "latest",
            "port": 25569,  # Nouveau port
            "eula": "true"
        }
    )
    assert response.status_code == 200
    assert "container_id" in response.json()

    # Vérifier que le dossier local a été créé dans ServerData
    data_dir = os.path.join(SERVER_DATA_DIR, server_name)
    assert os.path.exists(data_dir), f"Le dossier {data_dir} n'a pas été créé."

    # Nettoyer après le test
    shutil.rmtree(data_dir)

def test_delete_server_removes_data_directory():
    """ Vérifie que le dossier local dans ServerData est supprimé lors de la suppression d'un serveur """
    server_name = "test_server_to_delete_data_dir"
    create_response = client.post(
        "/create-server/",
        json={
            "server_name": server_name,
            "version": "latest",
            "port": 25570,  # Nouveau port
            "eula": "true"
        }
    )
    assert create_response.status_code == 200

    # Vérifier que le dossier local a été créé dans ServerData
    data_dir = os.path.join(SERVER_DATA_DIR, server_name)
    assert os.path.exists(data_dir), f"Le dossier {data_dir} n'a pas été créé."

    # Supprimer le serveur
    delete_response = client.post(f"/delete-server/{server_name}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": f"Server {server_name} deleted successfully"}

    # Vérifier que le dossier local a été supprimé
    assert not os.path.exists(data_dir), f"Le dossier {data_dir} n'a pas été supprimé."

def test_delete_server_removes_volumes():
    """ Vérifie que les volumes sont supprimés lors de la suppression d'un serveur """
    server_name = "test_server_to_delete_volumes"
    create_response = client.post(
        "/create-server/",
        json={
            "server_name": server_name,
            "version": "latest",
            "port": 25571,  # Nouveau port
            "eula": "true"
        }
    )
    assert create_response.status_code == 200

    # Récupérer le conteneur avec le client Docker
    docker_client = docker.from_env()
    container_id = create_response.json()["container_id"]
    container = docker_client.containers.get(container_id)

    # Vérifier que le conteneur a des volumes (montages de dossiers locaux)
    volumes = container.attrs["Mounts"]
    assert len(volumes) > 0, "Le conteneur n'a pas de volumes."

    # Récupérer le chemin du dossier local
    data_dir = os.path.join(SERVER_DATA_DIR, server_name)
    assert os.path.exists(data_dir), f"Le dossier {data_dir} n'a pas été créé."

    # Supprimer le serveur via l'API
    delete_response = client.post(f"/delete-server/{server_name}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": f"Server {server_name} deleted successfully"}

    # Vérifier que le dossier local a été supprimé
    assert not os.path.exists(data_dir), f"Le dossier {data_dir} n'a pas été supprimé."

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """ Nettoie tous les serveurs et dossiers locaux après l'exécution des tests """
    yield  # Exécute les tests normalement
    response = client.get("/list-servers/")
    for server in response.json().get("servers", []):
        client.post(f"/delete-server/{server['name']}")
        # Supprimer le dossier local s'il existe
        data_dir = os.path.join(SERVER_DATA_DIR, server['name'])
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)