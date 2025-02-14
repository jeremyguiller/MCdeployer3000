import os
import shutil
from fastapi import FastAPI, HTTPException
import docker
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()
client = docker.from_env()

# Chemin du dossier ServerData
SERVER_DATA_DIR = os.path.join(os.getcwd(), "ServerData")

# Modèle Pydantic pour les variables d'environnement
class MinecraftServerConfig(BaseModel):
    server_name: str
    version: Optional[str] = "latest"
    port: Optional[int] = 25565
    eula: str = "true"
    difficulty: Optional[str] = None
    type: Optional[str] = None
    spiget_resources: Optional[str] = None
    mods: Optional[List[str]] = None
    ops: Optional[str] = None
    online_mode: Optional[str] = None
    enable_autopause: Optional[str] = None
    memory: Optional[str] = None
    view_distance: Optional[int] = None
    max_players: Optional[int] = None
    whitelist: Optional[str] = None
    mods_files: Optional[str] = None
    world: Optional[str] = None
    uid: Optional[int] = None
    gid: Optional[int] = None
    init_memory: Optional[str] = None
    max_memory: Optional[str] = None
    tz: Optional[str] = None
    enable_rolling_logs: Optional[bool] = None
    enable_jmx: Optional[bool] = None
    jmx_host: Optional[str] = None
    use_aikar_flags: Optional[bool] = None
    jvm_opts: Optional[str] = None
    jvm_xx_opts: Optional[str] = None
    jvm_dd_opts: Optional[str] = None
    extra_args: Optional[str] = None
    log_timestamp: Optional[bool] = None
    motd: Optional[str] = None
    icon: Optional[str] = None
    rcon_password: Optional[str] = None
    rcon_port: Optional[int] = None
    enable_rcon: Optional[bool] = None
    enable_whitelist: Optional[bool] = None
    enforce_whitelist: Optional[bool] = None
    broadcast_rcon_to_ops: Optional[bool] = None
    enable_query: Optional[bool] = None
    query_port: Optional[int] = None
    level_seed: Optional[str] = None
    generator_settings: Optional[str] = None
    level_type: Optional[str] = None
    level: Optional[str] = None
    pvp: Optional[bool] = None
    hardcore: Optional[bool] = None
    allow_flight: Optional[bool] = None
    max_build_height: Optional[int] = None
    force_gamemode: Optional[bool] = None
    max_tick_time: Optional[int] = None
    max_world_size: Optional[int] = None
    spawn_npcs: Optional[bool] = None
    spawn_animals: Optional[bool] = None
    spawn_monsters: Optional[bool] = None
    spawn_protection: Optional[int] = None
    function_permission_level: Optional[int] = None
    network_compression_threshold: Optional[int] = None
    player_idle_timeout: Optional[int] = None
    rate_limit: Optional[int] = None
    enable_status: Optional[bool] = None
    sync_chunk_writes: Optional[bool] = None
    text_filtering_config: Optional[str] = None
    use_native_transport: Optional[bool] = None
    prevent_proxy_connections: Optional[bool] = None
    enable_jmx_monitoring: Optional[bool] = None
    resource_pack: Optional[str] = None
    resource_pack_sha1: Optional[str] = None
    resource_pack_prompt: Optional[str] = None
    resource_pack_required: Optional[bool] = None
    snooper_enabled: Optional[bool] = None
    entity_broadcast_range_percentage: Optional[int] = None
    simulation_distance: Optional[int] = None
    hide_online_players: Optional[bool] = None
    broadcast_console_to_ops: Optional[bool] = None
    enable_command_block: Optional[bool] = None
    op_permission_level: Optional[int] = None
    allow_nether: Optional[bool] = None

@app.post("/create-server/")
async def create_server(config: MinecraftServerConfig):
    try:
        # Créer le dossier ServerData s'il n'existe pas
        os.makedirs(SERVER_DATA_DIR, exist_ok=True)

        # Chemin du dossier local pour ce serveur
        data_dir = os.path.join(SERVER_DATA_DIR, config.server_name)
        os.makedirs(data_dir, exist_ok=True)

        # Convertir les mods en une chaîne séparée par des sauts de ligne si spécifiés
        mods_str = "\n".join(config.mods) if config.mods else None

        # Préparer les variables d'environnement
        environment = {
            key.upper(): str(value)
            for key, value in config.model_dump(exclude={"server_name", "port"}).items()
            if value is not None
        }
        if mods_str:
            environment['MODS'] = mods_str

        # Créer un conteneur Minecraft avec le dossier /data mappé
        container = client.containers.run(
            image=f"itzg/minecraft-server:{config.version}",
            name=config.server_name,
            ports={'25565/tcp': config.port},
            environment=environment,
            volumes={data_dir: {'bind': '/data', 'mode': 'rw'}},  # Mapper le dossier /data
            detach=True,
            stdin_open=True,
            tty=True,
            restart_policy={"Name": "always"}
        )
        return {"message": f"Server {config.server_name} created successfully", "container_id": container.id}
    except docker.errors.ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Minecraft server image for version {config.version} not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # En cas d'erreur, supprimer le dossier créé
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-servers/")
async def list_servers():
    try:
        containers = client.containers.list(all=True)
        servers = []
        for c in containers:
            # Récupérer les ports exposés par le conteneur
            ports = c.attrs["HostConfig"]["PortBindings"]
            server_port = None
            if ports and "25565/tcp" in ports:
                server_port = int(ports["25565/tcp"][0]["HostPort"])
            servers.append({
                "name": c.name,
                "id": c.id,
                "status": c.status,
                "port": server_port  # Ajouter le port utilisé
            })
        return {"servers": servers}
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-server/{server_name}")
async def stop_server(server_name: str):
    try:
        container = client.containers.get(server_name)
        container.stop()
        return {"message": f"Server {server_name} stopped successfully"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restart-server/{server_name}")
async def restart_server(server_name: str):
    try:
        container = client.containers.get(server_name)
        container.restart()
        return {"message": f"Server {server_name} restarted successfully"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete-server/{server_name}")
async def delete_server(server_name: str):
    try:
        # Récupérer le conteneur
        container = client.containers.get(server_name)

        # Arrêter et supprimer le conteneur
        container.stop()
        container.remove(v=True)  # Supprimer les volumes associés

        # Supprimer le dossier local dans ServerData
        data_dir = os.path.join(SERVER_DATA_DIR, server_name)
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

        return {"message": f"Server {server_name} deleted successfully"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)