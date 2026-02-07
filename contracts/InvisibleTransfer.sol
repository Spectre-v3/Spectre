// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}

/**
 * @title InvisibleTransfer
 * @dev Contrato principal para transacciones invisibles usando hashes
 * @notice Permite ocultar dirección destino y monto mediante hashing off-chain
 */
contract InvisibleTransfer {
    struct HiddenTransfer {
        address sender;
        address token;
        uint256 amount;
        uint256 timestamp;
        bool claimed;
    }
    
    // Mapping de hash a transferencia oculta
    mapping(bytes32 => HiddenTransfer) public hiddenTransfers;
    
    // Mapping de usuario a sus hashes de transferencias enviadas
    mapping(address => bytes32[]) public userSentTransfers;
    
    // Mapping de usuario a sus hashes de transferencias recibidas (una vez reclamadas)
    mapping(address => bytes32[]) public userReceivedTransfers;
    
    address public owner;
    uint256 public totalTransfers;
    uint256 public totalClaimed;
    
    // Fees
    uint256 public platformFee; // En basis points (100 = 1%)
    address public feeCollector;
    
    event TransferPublished(bytes32 indexed hash, address indexed sender, address token, uint256 amount);
    event TransferClaimed(bytes32 indexed hash, address indexed recipient, uint256 amount);
    event TransferCancelled(bytes32 indexed hash, address indexed sender);
    event FeeUpdated(uint256 newFee);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(uint256 _platformFee) {
        owner = msg.sender;
        feeCollector = msg.sender;
        platformFee = _platformFee; // Ejemplo: 50 = 0.5%
    }
    
    /**
     * @dev Publica una transferencia oculta usando un hash
     * @param _hash Hash SHA-256 generado off-chain con salt
     * @param _token Dirección del token ERC20
     * @param _amount Cantidad de tokens a transferir
     */
    function publishHiddenTransfer(
        bytes32 _hash,
        address _token,
        uint256 _amount
    ) external payable {
        require(_amount > 0, "Amount must be positive");
        require(hiddenTransfers[_hash].timestamp == 0, "Hash already exists");
        require(_token != address(0), "Invalid token address");
        
        // Calcular fee
        uint256 fee = (_amount * platformFee) / 10000;
        uint256 amountAfterFee = _amount - fee;
        
        // Transferir tokens al contrato
        require(
            IERC20(_token).transferFrom(msg.sender, address(this), _amount),
            "Token transfer failed"
        );
        
        // Transferir fee al collector si hay fee
        if (fee > 0) {
            require(
                IERC20(_token).transfer(feeCollector, fee),
                "Fee transfer failed"
            );
        }
        
        // Registrar transferencia oculta
        hiddenTransfers[_hash] = HiddenTransfer({
            sender: msg.sender,
            token: _token,
            amount: amountAfterFee,
            timestamp: block.timestamp,
            claimed: false
        });
        
        // Agregar a lista de transferencias del sender
        userSentTransfers[msg.sender].push(_hash);
        totalTransfers++;
        
        emit TransferPublished(_hash, msg.sender, _token, amountAfterFee);
    }
    
    /**
     * @dev Reclama una transferencia oculta usando el hash
     * @param _hash Hash de la transferencia a reclamar
     */
    function claimHiddenTransfer(bytes32 _hash) external {
        HiddenTransfer storage transfer = hiddenTransfers[_hash];
        
        require(transfer.timestamp > 0, "Transfer does not exist");
        require(!transfer.claimed, "Already claimed");
        require(transfer.amount > 0, "No amount to claim");
        
        // Marcar como reclamada
        transfer.claimed = true;
        totalClaimed++;
        
        // Agregar a lista de transferencias recibidas
        userReceivedTransfers[msg.sender].push(_hash);
        
        // Transferir tokens al reclamante
        require(
            IERC20(transfer.token).transfer(msg.sender, transfer.amount),
            "Claim transfer failed"
        );
        
        emit TransferClaimed(_hash, msg.sender, transfer.amount);
    }
    
    /**
     * @dev Permite al sender cancelar una transferencia no reclamada después de un período
     * @param _hash Hash de la transferencia a cancelar
     */
    function cancelHiddenTransfer(bytes32 _hash) external {
        HiddenTransfer storage transfer = hiddenTransfers[_hash];
        
        require(transfer.sender == msg.sender, "Not the sender");
        require(!transfer.claimed, "Already claimed");
        require(block.timestamp >= transfer.timestamp + 7 days, "Too early to cancel");
        
        uint256 amountToReturn = transfer.amount;
        address tokenToReturn = transfer.token;
        
        // Marcar como reclamada para evitar doble gasto
        transfer.claimed = true;
        
        // Devolver tokens al sender
        require(
            IERC20(tokenToReturn).transfer(msg.sender, amountToReturn),
            "Cancel transfer failed"
        );
        
        emit TransferCancelled(_hash, msg.sender);
    }
    
    /**
     * @dev Obtiene información de una transferencia oculta
     */
    function getHiddenTransfer(bytes32 _hash) external view returns (
        address sender,
        address token,
        uint256 amount,
        uint256 timestamp,
        bool claimed
    ) {
        HiddenTransfer memory transfer = hiddenTransfers[_hash];
        return (
            transfer.sender,
            transfer.token,
            transfer.amount,
            transfer.timestamp,
            transfer.claimed
        );
    }
    
    /**
     * @dev Obtiene todas las transferencias enviadas por un usuario
     */
    function getUserSentTransfers(address user) external view returns (bytes32[] memory) {
        return userSentTransfers[user];
    }
    
    /**
     * @dev Obtiene todas las transferencias recibidas por un usuario
     */
    function getUserReceivedTransfers(address user) external view returns (bytes32[] memory) {
        return userReceivedTransfers[user];
    }
    
    /**
     * @dev Actualiza el fee de la plataforma
     */
    function updatePlatformFee(uint256 _newFee) external onlyOwner {
        require(_newFee <= 500, "Fee too high"); // Max 5%
        platformFee = _newFee;
        emit FeeUpdated(_newFee);
    }
    
    /**
     * @dev Actualiza el collector de fees
     */
    function updateFeeCollector(address _newCollector) external onlyOwner {
        require(_newCollector != address(0), "Invalid address");
        feeCollector = _newCollector;
    }
    
    /**
     * @dev Función de emergencia para recuperar tokens atascados
     */
    function emergencyWithdraw(address _token, uint256 _amount) external onlyOwner {
        require(
            IERC20(_token).transfer(owner, _amount),
            "Emergency withdrawal failed"
        );
    }
    
    /**
     * @dev Obtiene estadísticas del contrato
     */
    function getStats() external view returns (
        uint256 total,
        uint256 claimed,
        uint256 pending
    ) {
        return (totalTransfers, totalClaimed, totalTransfers - totalClaimed);
    }
}
