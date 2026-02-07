# Guía de Desarrollo Spectre

## Configuración del Entorno de Desarrollo

### Herramientas Necesarias

1. **VS Code** (recomendado)
   - Extensiones:
     - Solidity (Juan Blanco)
     - Python (Microsoft)
     - Prettier
     - ESLint

2. **Terminal Tools**
   - Git
   - curl
   - jq (opcional, para debugging)

### Primera Configuración

```bash
# 1. Clonar repositorio
git clone https://github.com/Spectre-v3/Spectre.git
cd Spectre

# 2. Hacer ejecutable el script de deployment
chmod +x deploy.sh

# 3. Ejecutar deployment
./deploy.sh
```

## Desarrollo de Contratos

### Comandos Útiles

```bash
cd contracts

# Compilar
forge build

# Tests
forge test -vvv

# Test específico
forge test --match-test testPublishHiddenTransfer

# Gas report
forge test --gas-report

# Coverage
forge coverage

# Formatear código
forge fmt
```

### Estructura de Tests

```solidity
contract InvisibleTransferTest is Test {
    InvisibleTransfer public invisibleTransfer;
    MockERC20 public token;
    
    function setUp() public {
        // Setup inicial
    }
    
    function testNombreDelTest() public {
        // Tu test aquí
    }
}
```

### Deployment Local

```bash
# 1. Iniciar Anvil (blockchain local)
anvil

# 2. En otra terminal, desplegar
forge script scripts/Deploy.s.sol \
  --rpc-url http://localhost:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast
```

## Desarrollo Backend

### Estructura del Código

```python
# Patrón de endpoint en main.py
@app.post("/api/endpoint-name")
async def endpoint_name(request: RequestModel):
    try:
        # Lógica aquí
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Testing Backend

```bash
cd backend

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest tests/ -v

# Con coverage
pytest --cov=. tests/
```

### Ejecutar en Modo Desarrollo

```bash
cd backend
source venv/bin/activate

# Con auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Acceder a docs interactivas
# http://localhost:8000/docs
```

### Estructura de Tests Backend

```python
# tests/test_crypto_utils.py
import pytest
from crypto_utils import PrivacyEngine

def test_generate_hidden_transaction():
    engine = PrivacyEngine()
    result = engine.generate_hidden_transaction(
        sender="0x123...",
        recipient="0x456...",
        amount=100.0,
        token="USDC"
    )
    assert result["hash"].startswith("0x")
    assert len(result["salt"]) == 64
```

## Desarrollo Frontend

### Estructura del Código

```javascript
// Patrón de función en app.js
async function nombreDeFuncion() {
    if (!walletManager.isConnected) {
        showToast('Conecta tu wallet primero', 'warning');
        return;
    }
    
    try {
        showLoading('Procesando...');
        
        // Lógica aquí
        
        hideLoading();
        showToast('Éxito', 'success');
    } catch (error) {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    }
}
```

### Servir Frontend

```bash
cd frontend

# Opción 1: Python
python -m http.server 8080

# Opción 2: npx serve
npx serve . -p 8080

# Opción 3: npm http-server
npm install -g http-server
http-server -p 8080
```

### Debugging Frontend

```javascript
// Activar logs detallados en consola
localStorage.setItem('debug', 'true');

// En app.js, agregar:
const DEBUG = localStorage.getItem('debug') === 'true';
if (DEBUG) console.log('Debug info:', data);
```

## Flujo de Trabajo Git

### Branching Strategy

```
main         → Código producción
  ↓
develop      → Desarrollo activo
  ↓
feature/*    → Nuevas características
bugfix/*     → Corrección de bugs
hotfix/*     → Correcciones urgentes
```

### Comandos Git Comunes

```bash
# Crear feature branch
git checkout -b feature/nueva-funcionalidad

# Hacer cambios
git add .
git commit -m "feat: descripción del cambio"

# Push
git push origin feature/nueva-funcionalidad

# Crear PR en GitHub
```

### Convención de Commits

```
feat: nueva característica
fix: corrección de bug
docs: cambios en documentación
style: formateo, punto y coma faltante, etc
refactor: refactorización de código
test: agregar tests
chore: mantenimiento
```

## Testing Integración Completa

### Escenario de Test End-to-End

```bash
# 1. Iniciar backend
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# 2. Servir frontend
cd ../frontend
python -m http.server 8080 &
FRONTEND_PID=$!

# 3. Ejecutar tests E2E (si están configurados)
# npm run test:e2e

# 4. Limpiar
kill $BACKEND_PID
kill $FRONTEND_PID
```

## Debugging

### Backend Debugging

```python
# En main.py, agregar:
import logging
logging.basicConfig(level=logging.DEBUG)

# O usar pdb
import pdb; pdb.set_trace()
```

### Contratos Debugging

```bash
# Ejecutar con logs detallados
forge test -vvvv

# Ver eventos emitidos
forge test --decode-internal
```

### Frontend Debugging

```javascript
// En browser console
walletManager  // Inspeccionar estado del wallet
appState       // Inspeccionar estado de la app
apiClient      // Inspeccionar cliente API
```

## Performance

### Optimización de Contratos

```bash
# Optimizar con via-ir
forge build --via-ir

# Analizar gas
forge test --gas-report
```

### Optimización Backend

```python
# Usar cache para operaciones frecuentes
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    # ...
```

## Troubleshooting

### Error: "Network mismatch"

```javascript
// Verificar chainId en frontend/app.js
const expectedChainId = 11155111; // Sepolia
```

### Error: "InsufficientAllowance"

```javascript
// Verificar aprobación de tokens
await walletManager.checkAndApproveToken(
    tokenAddress,
    contractAddress,
    amount
);
```

### Error: "Connection refused" en backend

```bash
# Verificar que el puerto está libre
lsof -i :8000

# Cambiar puerto si es necesario
uvicorn main:app --port 8001
```

## Recursos Adicionales

- [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)
- [Python PEP 8](https://pep8.org/)
- [JavaScript Standard Style](https://standardjs.com/)
- [Foundry Cheat Codes](https://book.getfoundry.sh/cheatcodes/)

## Contacto y Soporte

- GitHub Issues: https://github.com/Spectre-v3/Spectre/issues
- Discord: [Link a Discord]
- Email: dev@spectre.example.com
