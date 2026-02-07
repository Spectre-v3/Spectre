# 👻 Spectre - Sistema de Transacciones Invisibles

> Transacciones privadas en blockchain usando hashing SHA-256 con salt + Integración Uniswap v4

[![Solidity](https://img.shields.io/badge/Solidity-0.8.19-blue)](https://soliditylang.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Descripción

**Spectre** es un sistema completo que permite realizar transacciones "invisibles" en blockchain, ocultando información sensible (dirección destino y monto) mediante hashing criptográfico con salt. El sistema integra con Uniswap v4 para proporcionar liquidez y privacidad adicional.

### Características Principales

- **Privacidad Total**: Hash SHA-256 con salt único para ocultar destino y monto
- **Verificación On-Chain**: Smart contracts validan sin revelar datos
- **Integración Uniswap v4**: Hooks personalizados para operaciones privadas
- **Interfaz Intuitiva**: Frontend completo con Web3/MetaMask
- **Backend Robusto**: FastAPI con gestión segura de hashes
- **Base de Datos**: SQLite para persistencia de transacciones

## Arquitectura del Sistema

```
┌─────────────────┐
│   Frontend      │  HTML/CSS/JS + ethers.js
│   (MetaMask)    │  Interfaz de usuario
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend       │  FastAPI (Python)
│   (Python)      │  Generación de hashes + DB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Smart          │  Solidity 0.8.19
│  Contracts      │  Gestión on-chain + Uniswap hooks
└─────────────────┘
```

### Componentes

1. **Frontend** (`frontend/`)
   - `index.html`: Interfaz principal
   - `styles.css`: Diseño moderno y responsive
   - `app.js`: Lógica de aplicación
   - `wallet.js`: Gestión de MetaMask
   - `api.js`: Cliente API

2. **Backend** (`backend/`)
   - `main.py`: Servidor FastAPI
   - `crypto_utils.py`: Funciones de hashing/cifrado
   - `database.py`: Gestión de base de datos SQLite
   - `uniswap_client.py`: Cliente Uniswap v4

3. **Smart Contracts** (`contracts/`)
   - `InvisibleTransfer.sol`: Contrato principal
   - `UniswapV4Hook.sol`: Hook de Uniswap v4
   - `TokenWrapper.sol`: Gestión de tokens

## Instalación Rápida

### Prerrequisitos

- Node.js 18+ y npm
- Python 3.10+
- Foundry (para contratos Solidity)
- MetaMask instalado en el navegador

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Spectre-v3/Spectre.git
cd Spectre
```

### 2. Configurar Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar servidor
python main.py
```

El backend estará disponible en `http://localhost:8000`

### 3. Desplegar Contratos

```bash
cd contracts

# Instalar Foundry (si no lo tienes)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Compilar contratos
forge build

# Ejecutar tests
forge test

# Desplegar en testnet (Sepolia)
forge script scripts/Deploy.s.sol:DeployInvisibleTransfer \
  --rpc-url $SEPOLIA_RPC_URL \
  --private-key $PRIVATE_KEY \
  --broadcast --verify
```

**Importante**: Guarda la dirección del contrato desplegado y actualízala en:
- `frontend/app.js` → variable `INVISIBLE_TRANSFER_CONTRACT`
- `backend/.env` → variable `INVISIBLE_TRANSFER_ADDRESS`

### 4. Configurar Frontend

```bash
cd frontend

# Actualizar dirección del contrato en app.js
# Línea 5: const INVISIBLE_TRANSFER_CONTRACT = '0x...';

# Servir con servidor HTTP simple
python -m http.server 8080
# O usar: npx serve .
```

Abrir navegador en `http://localhost:8080`

## Guía de Uso

### 1. Conectar Wallet

1. Abrir la aplicación en el navegador
2. Clic en "Conectar Wallet"
3. Aprobar conexión en MetaMask
4. Asegurar estar en Sepolia Testnet

### 2. Enviar Transacción Invisible

1. Ir a pestaña "Enviar"
2. Ingresar:
   - Dirección destinatario (0x...)
   - Cantidad de tokens
   - Seleccionar token (USDC, USDT, DAI, WETH)
3. Clic en "Crear Transacción Invisible"
4. Aprobar en MetaMask:
   - Primera tx: Aprobar tokens
   - Segunda tx: Publicar transacción invisible
5. ¡Listo! El hash se mostrará en pantalla

### 3. Reclamar Transacción

1. Ir a pestaña "Recibir"
2. Clic en "Actualizar" para ver transacciones pendientes
3. Si hay transacciones para ti, aparecerán listadas
4. Clic en "Reclamar"
5. Aprobar en MetaMask
6. Los tokens se transferirán a tu wallet

## Flujo Técnico Detallado

### Publicar Transacción Invisible

```javascript
// 1. Usuario ingresa datos en frontend
recipient = "0xBob..."
amount = 100
token = "USDC"

// 2. Frontend envía a backend
POST /api/generate-hash
{
  "sender": "0xAlice...",
  "recipient": "0xBob...",
  "amount": 100,
  "token": "USDC"
}

// 3. Backend genera hash
salt = random_32_bytes()
payload = "0xAlice:0xBob:100:USDC:salt:timestamp"
hash = SHA256(payload)  // 0xabc123...

// 4. Frontend llama a contrato
publishHiddenTransfer(hash, tokenAddress, amount)

// 5. Contrato guarda en blockchain
hiddenTransfers[hash] = {
  sender: 0xAlice,
  token: USDC,
  amount: 100,
  claimed: false
}
```

### Reclamar Transacción

```javascript
// 1. Bob consulta transacciones pendientes
GET /api/pending-transfers/0xBob...

// 2. Backend verifica si hay hashes para Bob
for hash in pending_hashes:
  if hash.recipient == "0xBob":
    return hash

// 3. Bob reclama en blockchain
claimHiddenTransfer(hash)

// 4. Contrato valida y transfiere
require(!hiddenTransfers[hash].claimed)
transfer(msg.sender, amount)
hiddenTransfers[hash].claimed = true
```

## 🧪 Testing

### Contratos Solidity

```bash
cd contracts

# Ejecutar todos los tests
forge test

# Tests con verbosidad
forge test -vvv

# Test específico
forge test --match-test testPublishHiddenTransfer

# Coverage
forge coverage
```

### Backend Python

```bash
cd backend

# Instalar pytest
pip install pytest pytest-asyncio

# Ejecutar tests (crear tests/)
pytest tests/ -v
```

## Estructura del Proyecto

```
Spectre/
├── README.md                    # Este archivo
├── frontend/                    # Aplicación web
│   ├── index.html              # Interfaz principal
│   ├── styles.css              # Estilos
│   ├── app.js                  # Lógica principal
│   ├── wallet.js               # Gestión MetaMask
│   └── api.js                  # Cliente API
├── backend/                     # Servidor Python
│   ├── main.py                 # FastAPI server
│   ├── crypto_utils.py         # Hashing/crypto
│   ├── database.py             # SQLite manager
│   ├── uniswap_client.py       # Cliente Uniswap
│   ├── requirements.txt        # Dependencias Python
│   ├── .env.example            # Variables de entorno
│   └── .gitignore
└── contracts/                   # Smart Contracts
    ├── InvisibleTransfer.sol   # Contrato principal
    ├── UniswapV4Hook.sol       # Hook Uniswap v4
    ├── TokenWrapper.sol        # Wrapper tokens
    ├── foundry.toml            # Config Foundry
    ├── scripts/
    │   └── Deploy.s.sol        # Script deployment
    ├── test/
    │   └── InvisibleTransfer.t.sol  # Tests
    └── .gitignore
```

## Configuración Avanzada

### Variables de Entorno Backend

```bash
# backend/.env
DATABASE_URL=sqlite:///./invisible_transfers.db
RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
CHAIN_ID=11155111

# Direcciones de contratos
INVISIBLE_TRANSFER_ADDRESS=0x...
POOL_MANAGER_ADDRESS=0x...
HOOK_ADDRESS=0x...

# API Config
API_HOST=0.0.0.0
API_PORT=8000
```

### Direcciones de Tokens (Sepolia)

Las direcciones están preconfiguradas en `frontend/api.js`:

```javascript
const TOKEN_ADDRESSES = {
  'USDC': '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
  'USDT': '0x2E8D98fd126a32362ab81e87810bE5238b2C0E57',
  'DAI': '0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6',
  'WETH': '0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14'
};
```

## Seguridad

### Consideraciones Importantes

**Este proyecto es para fines educativos en testnet**

Para producción:

1. **Auditar Contratos**: Contratar auditoría profesional
2. **Backend Seguro**: 
   - Usar HTTPS
   - Implementar rate limiting
   - Proteger salts con KMS
3. **Frontend**:
   - Validación exhaustiva de inputs
   - Sanitización de datos
4. **Base de Datos**:
   - Encriptar datos sensibles
   - Backups regulares
5. **Gas Optimization**: Optimizar contratos para reducir costos

### Vulnerabilidades Conocidas

- Backend almacena salts (usar HSM/KMS en producción)
- No hay autenticación de usuarios
- Rate limiting no implementado
- Frontend expone todas las configuraciones

## Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Recursos

- [Documentación Uniswap v4](https://docs.uniswap.org/contracts/v4/overview)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [ethers.js](https://docs.ethers.org/v5/)
- [Foundry Book](https://book.getfoundry.sh/)
- [Solidity Docs](https://docs.soliditylang.org/)

## Roadmap

- [x] Sistema básico de transacciones invisibles
- [x] Integración con MetaMask
- [x] Backend FastAPI
- [x] Smart contracts Solidity
- [ ] Hooks completos de Uniswap v4
- [ ] Soporte para múltiples redes
- [ ] Sistema de notificaciones
- [ ] Mobile responsive mejorado
- [ ] Integración con wallets adicionales
- [ ] Dashboard de analytics

## Autores

- **Spectre Team** - [GitHub](https://github.com/Spectre-v3)

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Disclaimer

**SOLO PARA FINES EDUCATIVOS Y TESTNET**

Este software se proporciona "tal cual", sin garantía de ningún tipo. No use en producción sin auditoría profesional. Los autores no son responsables por pérdidas o daños.


---