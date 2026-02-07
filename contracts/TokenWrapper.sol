// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

/**
 * @title TokenWrapper
 * @dev Wrapper para tokens estándar ERC20 con funcionalidad extendida
 * @notice Facilita la interacción con múltiples tokens en el sistema de transferencias invisibles
 */
contract TokenWrapper {
    
    struct TokenInfo {
        address tokenAddress;
        string symbol;
        uint8 decimals;
        bool isSupported;
    }
    
    // Mapping de símbolo a información de token
    mapping(string => TokenInfo) public supportedTokens;
    
    // Array de símbolos soportados
    string[] public tokenSymbols;
    
    address public owner;
    
    event TokenAdded(string indexed symbol, address indexed tokenAddress, uint8 decimals);
    event TokenRemoved(string indexed symbol);
    event TokensWrapped(address indexed user, address indexed token, uint256 amount);
    event TokensUnwrapped(address indexed user, address indexed token, uint256 amount);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Agrega un nuevo token soportado
     */
    function addSupportedToken(
        string memory _symbol,
        address _tokenAddress,
        uint8 _decimals
    ) external onlyOwner {
        require(_tokenAddress != address(0), "Invalid token address");
        require(!supportedTokens[_symbol].isSupported, "Token already supported");
        
        supportedTokens[_symbol] = TokenInfo({
            tokenAddress: _tokenAddress,
            symbol: _symbol,
            decimals: _decimals,
            isSupported: true
        });
        
        tokenSymbols.push(_symbol);
        
        emit TokenAdded(_symbol, _tokenAddress, _decimals);
    }
    
    /**
     * @dev Remueve un token soportado
     */
    function removeSupportedToken(string memory _symbol) external onlyOwner {
        require(supportedTokens[_symbol].isSupported, "Token not supported");
        
        supportedTokens[_symbol].isSupported = false;
        
        emit TokenRemoved(_symbol);
    }
    
    /**
     * @dev Obtiene la dirección de un token por su símbolo
     */
    function getTokenAddress(string memory _symbol) external view returns (address) {
        require(supportedTokens[_symbol].isSupported, "Token not supported");
        return supportedTokens[_symbol].tokenAddress;
    }
    
    /**
     * @dev Verifica si un token está soportado
     */
    function isTokenSupported(string memory _symbol) external view returns (bool) {
        return supportedTokens[_symbol].isSupported;
    }
    
    /**
     * @dev Obtiene todos los tokens soportados
     */
    function getAllSupportedTokens() external view returns (string[] memory) {
        return tokenSymbols;
    }
    
    /**
     * @dev Obtiene información completa de un token
     */
    function getTokenInfo(string memory _symbol) external view returns (
        address tokenAddress,
        string memory symbol,
        uint8 decimals,
        bool isSupported
    ) {
        TokenInfo memory info = supportedTokens[_symbol];
        return (info.tokenAddress, info.symbol, info.decimals, info.isSupported);
    }
    
    /**
     * @dev Wrapper de tokens - deposita tokens al contrato
     */
    function wrapTokens(string memory _symbol, uint256 _amount) external {
        require(supportedTokens[_symbol].isSupported, "Token not supported");
        require(_amount > 0, "Amount must be positive");
        
        address tokenAddress = supportedTokens[_symbol].tokenAddress;
        
        require(
            IERC20(tokenAddress).transferFrom(msg.sender, address(this), _amount),
            "Transfer failed"
        );
        
        emit TokensWrapped(msg.sender, tokenAddress, _amount);
    }
    
    /**
     * @dev Unwrap de tokens - retira tokens del contrato
     */
    function unwrapTokens(string memory _symbol, uint256 _amount) external {
        require(supportedTokens[_symbol].isSupported, "Token not supported");
        require(_amount > 0, "Amount must be positive");
        
        address tokenAddress = supportedTokens[_symbol].tokenAddress;
        
        require(
            IERC20(tokenAddress).transfer(msg.sender, _amount),
            "Transfer failed"
        );
        
        emit TokensUnwrapped(msg.sender, tokenAddress, _amount);
    }
    
    /**
     * @dev Obtiene el balance de tokens en el contrato
     */
    function getContractBalance(string memory _symbol) external view returns (uint256) {
        require(supportedTokens[_symbol].isSupported, "Token not supported");
        address tokenAddress = supportedTokens[_symbol].tokenAddress;
        return IERC20(tokenAddress).balanceOf(address(this));
    }
    
    /**
     * @dev Obtiene el balance de un usuario para un token específico
     */
    function getUserBalance(string memory _symbol, address _user) external view returns (uint256) {
        require(supportedTokens[_symbol].isSupported, "Token not supported");
        address tokenAddress = supportedTokens[_symbol].tokenAddress;
        return IERC20(tokenAddress).balanceOf(_user);
    }
    
    /**
     * @dev Función de emergencia para recuperar tokens
     */
    function emergencyWithdraw(address _token, uint256 _amount) external onlyOwner {
        require(
            IERC20(_token).transfer(owner, _amount),
            "Emergency withdrawal failed"
        );
    }
}
