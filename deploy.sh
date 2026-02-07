#!/bin/bash

# Script de deployment completo para Spectre
# Ejecutar con: bash deploy.sh

echo "🚀 Iniciando deployment de Spectre..."
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Ejecutar este script desde la raíz del proyecto${NC}"
    exit 1
fi

# 1. Backend Setup
echo -e "${YELLOW}📦 Step 1: Configurando Backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Instalando dependencias..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Copiando .env.example a .env..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Por favor edita backend/.env con tus configuraciones${NC}"
fi

echo -e "${GREEN}✅ Backend configurado${NC}"
cd ..

# 2. Contracts Setup
echo ""
echo -e "${YELLOW}📜 Step 2: Configurando Contratos...${NC}"
cd contracts

if ! command -v forge &> /dev/null; then
    echo -e "${RED}Foundry no está instalado. Instalando...${NC}"
    curl -L https://foundry.paradigm.xyz | bash
    foundryup
fi

echo "Compilando contratos..."
forge build

echo "Ejecutando tests..."
forge test

echo -e "${GREEN}✅ Contratos compilados y testeados${NC}"
cd ..

# 3. Frontend Setup
echo ""
echo -e "${YELLOW}🌐 Step 3: Configurando Frontend...${NC}"
echo "Frontend listo para servir"
echo -e "${GREEN}✅ Frontend configurado${NC}"

# Resumen
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment completado exitosamente!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Editar backend/.env con tus configuraciones"
echo ""
echo "2. Desplegar contratos en testnet:"
echo "   cd contracts"
echo "   forge script scripts/Deploy.s.sol:DeployInvisibleTransfer \\"
echo "     --rpc-url \$SEPOLIA_RPC_URL \\"
echo "     --private-key \$PRIVATE_KEY \\"
echo "     --broadcast --verify"
echo ""
echo "3. Actualizar dirección del contrato en:"
echo "   - frontend/app.js"
echo "   - backend/.env"
echo ""
echo "4. Iniciar backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "5. Servir frontend:"
echo "   cd frontend"
echo "   python -m http.server 8080"
echo ""
echo -e "${YELLOW}🎉 ¡Listo para usar Spectre!${NC}"
