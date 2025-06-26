
#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Auto Push Script iniciado...${NC}"

# Verificar si hay cambios
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✅ No hay cambios que hacer push${NC}"
    exit 0
fi

# Mostrar archivos modificados
echo -e "${BLUE}📝 Archivos modificados:${NC}"
git status --short

# Agregar todos los archivos
echo -e "${BLUE}📦 Agregando archivos...${NC}"
git add .

# Commit con timestamp automático
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto update: $TIMESTAMP"

echo -e "${BLUE}💾 Haciendo commit: $COMMIT_MSG${NC}"
git commit -m "$COMMIT_MSG"

# Push
echo -e "${BLUE}🚀 Enviando a GitHub...${NC}"
git push origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Push exitoso! Cambios enviados a GitHub${NC}"
    echo -e "${GREEN}🔄 Railway detectará los cambios y hará deploy automáticamente${NC}"
else
    echo -e "${RED}❌ Error en el push${NC}"
fi
