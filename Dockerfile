# Utiliser une image Python avec uv pré-installé
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Activer la compilation du bytecode
ENV UV_COMPILE_BYTECODE=1

# Copier depuis le cache au lieu de lier car c'est un volume monté
ENV UV_LINK_MODE=copy

# Installer les dépendances du projet en utilisant le fichier de verrouillage et les paramètres
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Ajouter le reste du code source du projet et l'installer
# Installer séparément de ses dépendances permet une mise en cache optimale des couches
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Placer les exécutables dans l'environnement au début du chemin
ENV PATH="/app/.venv/bin:$PATH"

# Réinitialiser le point d'entrée, ne pas invoquer `uv`
ENTRYPOINT []

# Exécuter l'application FastAPI par défaut
# Utilise `uvicorn` pour servir l'application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
