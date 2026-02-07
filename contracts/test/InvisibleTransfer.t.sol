// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../InvisibleTransfer.sol";

contract MockERC20 is Test {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }
    
    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        
        return true;
    }
    
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }
}

contract InvisibleTransferTest is Test {
    InvisibleTransfer public invisibleTransfer;
    MockERC20 public token;
    
    address public alice = address(0x1);
    address public bob = address(0x2);
    
    bytes32 public testHash = keccak256("test");
    
    function setUp() public {
        // Deploy contracts
        invisibleTransfer = new InvisibleTransfer(50); // 0.5% fee
        token = new MockERC20();
        
        // Mint tokens to Alice
        token.mint(alice, 1000 ether);
        
        // Setup Alice
        vm.prank(alice);
        token.approve(address(invisibleTransfer), type(uint256).max);
    }
    
    function testPublishHiddenTransfer() public {
        uint256 amount = 100 ether;
        
        vm.prank(alice);
        invisibleTransfer.publishHiddenTransfer(testHash, address(token), amount);
        
        (address sender, address tokenAddr, uint256 amt, , bool claimed) = 
            invisibleTransfer.getHiddenTransfer(testHash);
        
        assertEq(sender, alice);
        assertEq(tokenAddr, address(token));
        assertEq(claimed, false);
        assertTrue(amt > 0); // Should have amount minus fee
    }
    
    function testClaimHiddenTransfer() public {
        uint256 amount = 100 ether;
        
        // Alice publishes
        vm.prank(alice);
        invisibleTransfer.publishHiddenTransfer(testHash, address(token), amount);
        
        // Bob claims
        uint256 bobBalanceBefore = token.balanceOf(bob);
        
        vm.prank(bob);
        invisibleTransfer.claimHiddenTransfer(testHash);
        
        uint256 bobBalanceAfter = token.balanceOf(bob);
        
        assertTrue(bobBalanceAfter > bobBalanceBefore);
        
        (, , , , bool claimed) = invisibleTransfer.getHiddenTransfer(testHash);
        assertTrue(claimed);
    }
    
    function testCannotClaimTwice() public {
        uint256 amount = 100 ether;
        
        vm.prank(alice);
        invisibleTransfer.publishHiddenTransfer(testHash, address(token), amount);
        
        vm.prank(bob);
        invisibleTransfer.claimHiddenTransfer(testHash);
        
        // Try to claim again
        vm.prank(bob);
        vm.expectRevert("Already claimed");
        invisibleTransfer.claimHiddenTransfer(testHash);
    }
    
    function testCannotPublishSameHashTwice() public {
        uint256 amount = 100 ether;
        
        vm.prank(alice);
        invisibleTransfer.publishHiddenTransfer(testHash, address(token), amount);
        
        vm.prank(alice);
        vm.expectRevert("Hash already exists");
        invisibleTransfer.publishHiddenTransfer(testHash, address(token), amount);
    }
}
