#!/usr/bin/env bash
# Arma 19_cloud_run_api/build/ con todo lo que va dentro del contenedor.
# (El contenedor necesita comun/, que vive una carpeta arriba.)
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
BUILD="$AQUI/build"

rm -rf "$BUILD" && mkdir -p "$BUILD"
cp "$AQUI/app.py" "$AQUI/Dockerfile" "$AQUI/requirements.txt" "$BUILD/"
cp -r "$AQUI/../comun" "$BUILD/comun"
find "$BUILD" -name "__pycache__" -type d -prune -exec rm -rf {} +
printf '__pycache__/\n*.pyc\n.env\n' > "$BUILD/.dockerignore"
echo "Build listo en $BUILD"
