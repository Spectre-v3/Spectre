/**
 * api.js - Cliente para comunicación con el backend
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    /**
     * Realiza una petición HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (options.body) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({
                    detail: `HTTP error! status: ${response.status}`
                }));
                throw new Error(error.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    /**
     * Genera un hash para una transacción invisible
     */
    async generateHash(sender, recipient, amount, token) {
        return this.request('/api/generate-hash', {
            method: 'POST',
            body: {
                sender,
                recipient,
                amount: parseFloat(amount),
                token
            }
        });
    }

    /**
     * Verifica si una transacción es válida para un destinatario
     */
    async verifyTransaction(hash, recipient) {
        return this.request('/api/verify-transaction', {
            method: 'POST',
            body: {
                hash,
                recipient
            }
        });
    }

    /**
     * Obtiene el estado de una transacción
     */
    async getTransactionStatus(hash) {
        return this.request(`/api/transaction-status/${hash}`);
    }

    /**
     * Obtiene transacciones pendientes para una dirección
     */
    async getPendingTransfers(address) {
        return this.request(`/api/pending-transfers/${address}`);
    }

    /**
     * Marca una transacción como reclamada
     */
    async claimTransaction(hash, claimer) {
        return this.request('/api/claim-transaction', {
            method: 'POST',
            body: {
                hash,
                claimer
            }
        });
    }

    /**
     * Obtiene una cotización de Uniswap
     */
    async getUniswapQuote(tokenIn, tokenOut, amountIn, decimalsIn = 18) {
        return this.request('/api/uniswap/quote', {
            method: 'POST',
            body: {
                token_in: tokenIn,
                token_out: tokenOut,
                amount_in: parseFloat(amountIn),
                decimals_in: decimalsIn
            }
        });
    }

    /**
     * Obtiene estadísticas generales
     */
    async getStats() {
        return this.request('/api/stats');
    }

    /**
     * Obtiene estadísticas de un usuario
     */
    async getUserStats(address) {
        return this.request(`/api/user-stats/${address}`);
    }

    /**
     * Health check del backend
     */
    async healthCheck() {
        return this.request('/health');
    }
}

// Instancia global del cliente API
const apiClient = new APIClient();

/**
 * Configuraciones de tokens conocidos
 */
const TOKEN_ADDRESSES = {
    // Sepolia Testnet
    'USDC': '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
    'USDT': '0x2E8D98fd126a32362ab81e87810bE5238b2C0E57',
    'DAI': '0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6',
    'WETH': '0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14',
    
    // Mainnet (para referencia)
    // 'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    // 'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    // 'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    // 'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
};

/**
 * Configuración de decimales por token
 */
const TOKEN_DECIMALS = {
    'USDC': 6,
    'USDT': 6,
    'DAI': 18,
    'WETH': 18
};

/**
 * Obtiene la dirección de un token por su símbolo
 */
function getTokenAddress(symbol) {
    return TOKEN_ADDRESSES[symbol] || null;
}

/**
 * Obtiene los decimales de un token
 */
function getTokenDecimals(symbol) {
    return TOKEN_DECIMALS[symbol] || 18;
}
