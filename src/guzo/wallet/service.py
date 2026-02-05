"""Wallet domain service - business logic for token-based payments."""

from datetime import datetime
from typing import Optional, List
from beanie import PydanticObjectId

from src.guzo.wallet.core import (
    DriverWallet,
    TokenTransaction,
    TokenPackage,
    PlatformFeeConfig,
    TokenTransactionType,
    WalletResponse,
    TransactionResponse,
    PackageResponse,
    FeeConfigResponse,
    CreatePackageRequest,
    UpdatePackageRequest,
    UpdateFeeConfigRequest,
)
from src.guzo.wallet.repository import (
    wallet_repository,
    transaction_repository,
    package_repository,
    fee_config_repository,
)
from src.guzo.auth.core import User, UserRole


class InsufficientTokensError(Exception):
    """Raised when driver doesn't have enough tokens."""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient tokens: need {required}, have {available}"
        )


class WalletService:
    """Service for managing driver wallets and token transactions."""
    
    # ============== Wallet Operations ==============
    
    @staticmethod
    async def get_or_create_wallet(driver_id: str) -> DriverWallet:
        """Get existing wallet or create a new one for driver."""
        # Validate driver exists and is actually a driver
        try:
            driver = await User.get(PydanticObjectId(driver_id))
        except Exception:
            raise ValueError("Invalid driver ID format")
        
        if not driver:
            raise ValueError("Driver not found")
        
        if driver.role != UserRole.DRIVER:
            raise ValueError("User is not a driver")
        
        return await wallet_repository.get_or_create(driver_id)
    
    @staticmethod
    async def get_wallet(driver_id: str) -> Optional[DriverWallet]:
        """Get wallet for a driver."""
        return await wallet_repository.get_by_driver_id(driver_id)
    
    @staticmethod
    async def get_wallet_response(driver_id: str) -> Optional[WalletResponse]:
        """Get wallet response for a driver."""
        wallet = await wallet_repository.get_by_driver_id(driver_id)
        if not wallet:
            return None
        return WalletService._wallet_to_response(wallet)
    
    @staticmethod
    async def update_wallet_settings(
        driver_id: str,
        low_balance_threshold: int
    ) -> DriverWallet:
        """Update wallet settings (driver can update their threshold)."""
        wallet = await wallet_repository.get_or_create(driver_id)
        wallet.low_balance_threshold = low_balance_threshold
        wallet.updated_at = datetime.utcnow()
        await wallet.save()
        return wallet
    
    @staticmethod
    async def check_balance_for_trip(
        driver_id: str,
        expected_seats: int = 1
    ) -> dict:
        """
        Check if driver has enough tokens to complete a trip.
        
        Returns dict with:
        - can_accept: bool
        - token_balance: int
        - estimated_fee: int
        - minimum_required: int
        """
        wallet = await wallet_repository.get_by_driver_id(driver_id)
        fee_config = await fee_config_repository.get_or_create_default()
        
        if not wallet:
            return {
                "can_accept": False,
                "token_balance": 0,
                "estimated_fee": fee_config.calculate_fee(expected_seats),
                "minimum_required": fee_config.minimum_balance_required,
                "reason": "No wallet found - contact admin",
            }
        
        estimated_fee = fee_config.calculate_fee(expected_seats)
        can_accept = (
            wallet.is_active and
            wallet.token_balance >= fee_config.minimum_balance_required and
            wallet.token_balance >= estimated_fee
        )
        
        result = {
            "can_accept": can_accept,
            "token_balance": wallet.token_balance,
            "estimated_fee": estimated_fee,
            "minimum_required": fee_config.minimum_balance_required,
        }
        
        if not can_accept:
            if not wallet.is_active:
                result["reason"] = "Wallet is inactive"
            elif wallet.token_balance < fee_config.minimum_balance_required:
                result["reason"] = f"Balance below minimum required ({fee_config.minimum_balance_required} tokens)"
            else:
                result["reason"] = f"Need at least {estimated_fee} tokens for this trip"
        
        return result
    
    # ============== Token Credit Operations ==============
    
    @staticmethod
    async def sell_tokens(
        driver_id: str,
        package_id: str,
        payment_reference: str,
        admin_id: str,
        notes: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Admin sells tokens to a driver.
        
        Args:
            driver_id: The driver to credit
            package_id: The token package purchased
            payment_reference: Receipt/bank reference number
            admin_id: Admin who processed the purchase
            notes: Optional notes
            
        Returns:
            TokenTransaction record
        """
        # Get the package
        try:
            package = await TokenPackage.get(PydanticObjectId(package_id))
        except Exception:
            raise ValueError("Invalid package ID format")
        
        if not package:
            raise ValueError("Token package not found")
        
        if not package.is_active:
            raise ValueError("Token package is no longer available")
        
        # Get or create wallet
        wallet = await WalletService.get_or_create_wallet(driver_id)
        
        # Calculate total tokens
        total_tokens = package.total_tokens
        
        # Credit the tokens
        transaction = await wallet_repository.update_balance_atomic(
            wallet_id=str(wallet.id),
            amount=total_tokens,
            transaction_type=TokenTransactionType.PURCHASE,
            description=f"Purchased {package.name} package ({total_tokens} tokens)",
            payment_reference=payment_reference,
            payment_amount_etb=package.price_etb,
            admin_id=admin_id,
            notes=notes,
        )
        
        if not transaction:
            raise ValueError("Failed to credit tokens")
        
        return transaction
    
    @staticmethod
    async def credit_bonus(
        driver_id: str,
        amount: int,
        description: str,
        admin_id: str,
        notes: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Admin credits bonus tokens to a driver.
        
        Args:
            driver_id: The driver to credit
            amount: Number of bonus tokens (must be positive)
            description: Reason for the bonus
            admin_id: Admin who approved the bonus
            notes: Optional notes
        """
        if amount <= 0:
            raise ValueError("Bonus amount must be positive")
        
        wallet = await WalletService.get_or_create_wallet(driver_id)
        
        transaction = await wallet_repository.update_balance_atomic(
            wallet_id=str(wallet.id),
            amount=amount,
            transaction_type=TokenTransactionType.BONUS,
            description=description,
            admin_id=admin_id,
            notes=notes,
        )
        
        if not transaction:
            raise ValueError("Failed to credit bonus tokens")
        
        return transaction
    
    @staticmethod
    async def manual_adjustment(
        driver_id: str,
        amount: int,
        description: str,
        admin_id: str,
        notes: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Admin makes a manual adjustment (credit or debit).
        
        Args:
            driver_id: The driver
            amount: Positive for credit, negative for debit
            description: Reason for adjustment
            admin_id: Admin who made the adjustment
            notes: Optional notes
        """
        if amount == 0:
            raise ValueError("Adjustment amount cannot be zero")
        
        wallet = await WalletService.get_or_create_wallet(driver_id)
        
        transaction = await wallet_repository.update_balance_atomic(
            wallet_id=str(wallet.id),
            amount=amount,
            transaction_type=TokenTransactionType.ADJUSTMENT,
            description=description,
            admin_id=admin_id,
            notes=notes,
        )
        
        if not transaction:
            raise InsufficientTokensError(
                required=abs(amount),
                available=wallet.token_balance
            )
        
        return transaction
    
    # ============== Token Debit Operations ==============
    
    @staticmethod
    async def charge_trip_fee(
        driver_id: str,
        trip_id: str,
        booked_seats: int,
    ) -> TokenTransaction:
        """
        Charge driver for a completed trip.
        
        Args:
            driver_id: The driver who completed the trip
            trip_id: The completed trip ID
            booked_seats: Number of seats that were booked
            
        Returns:
            TokenTransaction record
            
        Raises:
            InsufficientTokensError: If driver doesn't have enough tokens
            ValueError: If wallet not found
        """
        wallet = await wallet_repository.get_by_driver_id(driver_id)
        if not wallet:
            raise ValueError("Driver wallet not found")
        
        if not wallet.is_active:
            raise ValueError("Driver wallet is inactive")
        
        # Get fee configuration
        fee_config = await fee_config_repository.get_or_create_default()
        fee_amount = fee_config.calculate_fee(booked_seats)
        
        if fee_amount == 0:
            # No fee to charge
            return None
        
        # Charge the fee (negative amount)
        transaction = await wallet_repository.update_balance_atomic(
            wallet_id=str(wallet.id),
            amount=-fee_amount,
            transaction_type=TokenTransactionType.TRIP_FEE,
            description=f"Platform fee for trip ({booked_seats} seats)",
            trip_id=trip_id,
            booking_count=booked_seats,
        )
        
        if not transaction:
            raise InsufficientTokensError(
                required=fee_amount,
                available=wallet.token_balance
            )
        
        return transaction
    
    @staticmethod
    async def refund_trip_fee(
        driver_id: str,
        trip_id: str,
        original_fee: int,
        reason: str,
        admin_id: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Refund tokens for a cancelled trip.
        
        Args:
            driver_id: The driver
            trip_id: The cancelled trip ID
            original_fee: The fee that was charged
            reason: Reason for refund
            admin_id: Admin who approved (optional)
        """
        wallet = await wallet_repository.get_by_driver_id(driver_id)
        if not wallet:
            raise ValueError("Driver wallet not found")
        
        transaction = await wallet_repository.update_balance_atomic(
            wallet_id=str(wallet.id),
            amount=original_fee,  # Positive to credit back
            transaction_type=TokenTransactionType.REFUND,
            description=f"Refund for trip: {reason}",
            trip_id=trip_id,
            admin_id=admin_id,
        )
        
        return transaction
    
    # ============== Transaction History ==============
    
    @staticmethod
    async def get_transaction_history(
        driver_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[TransactionResponse]:
        """Get transaction history for a driver."""
        transactions = await transaction_repository.get_by_driver_id(
            driver_id, limit, offset
        )
        return [WalletService._transaction_to_response(t) for t in transactions]
    
    @staticmethod
    async def get_transaction_count(driver_id: str) -> int:
        """Get total transaction count for pagination."""
        return await transaction_repository.count_by_driver(driver_id)
    
    # ============== Package Operations ==============
    
    @staticmethod
    async def get_available_packages() -> List[PackageResponse]:
        """Get all active token packages."""
        packages = await package_repository.get_active_packages()
        return [WalletService._package_to_response(p) for p in packages]
    
    @staticmethod
    async def create_package(data: CreatePackageRequest) -> TokenPackage:
        """Create a new token package (admin only)."""
        # Check if name is unique
        existing = await package_repository.get_by_name(data.name)
        if existing:
            raise ValueError(f"Package with name '{data.name}' already exists")
        
        package = TokenPackage(
            name=data.name,
            description=data.description,
            tokens=data.tokens,
            bonus_tokens=data.bonus_tokens,
            price_etb=data.price_etb,
            sort_order=data.sort_order,
        )
        await package.insert()
        return package
    
    @staticmethod
    async def update_package(
        package_id: str,
        data: UpdatePackageRequest
    ) -> Optional[TokenPackage]:
        """Update a token package (admin only)."""
        try:
            package = await TokenPackage.get(PydanticObjectId(package_id))
        except Exception:
            raise ValueError("Invalid package ID format")
        
        if not package:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(package, key, value)
        
        package.updated_at = datetime.utcnow()
        await package.save()
        return package
    
    @staticmethod
    async def delete_package(package_id: str) -> bool:
        """Delete a token package (admin only)."""
        try:
            package = await TokenPackage.get(PydanticObjectId(package_id))
        except Exception:
            return False
        
        if not package:
            return False
        
        await package.delete()
        return True
    
    # ============== Fee Configuration ==============
    
    @staticmethod
    async def get_fee_config() -> FeeConfigResponse:
        """Get current fee configuration."""
        config = await fee_config_repository.get_or_create_default()
        return FeeConfigResponse(
            fee_per_seat=config.fee_per_seat,
            fee_per_trip=config.fee_per_trip,
            minimum_balance_required=config.minimum_balance_required,
        )
    
    @staticmethod
    async def update_fee_config(data: UpdateFeeConfigRequest) -> PlatformFeeConfig:
        """Update fee configuration (admin only)."""
        update_data = data.model_dump(exclude_unset=True)
        return await fee_config_repository.update(update_data)
    
    # ============== Admin Dashboard ==============
    
    @staticmethod
    async def get_recent_purchases(limit: int = 50) -> List[TransactionResponse]:
        """Get recent token purchases (admin dashboard)."""
        transactions = await transaction_repository.get_recent_purchases(limit)
        return [WalletService._transaction_to_response(t) for t in transactions]
    
    @staticmethod
    async def get_low_balance_drivers() -> List[WalletResponse]:
        """Get drivers with low balance (admin alerts)."""
        wallets = await wallet_repository.get_low_balance_wallets()
        return [WalletService._wallet_to_response(w) for w in wallets]
    
    @staticmethod
    async def get_platform_token_stats() -> dict:
        """Get platform-wide token statistics."""
        wallets = await wallet_repository.get_all_active()
        
        total_balance = sum(w.token_balance for w in wallets)
        total_purchased = sum(w.total_purchased for w in wallets)
        total_spent = sum(w.total_spent for w in wallets)
        total_bonus = sum(w.total_bonus for w in wallets)
        
        low_balance_count = len([w for w in wallets if w.is_low_balance])
        
        return {
            "total_wallets": len(wallets),
            "total_balance_in_circulation": total_balance,
            "total_tokens_sold": total_purchased,
            "total_tokens_spent": total_spent,
            "total_bonus_given": total_bonus,
            "low_balance_drivers": low_balance_count,
        }
    
    # ============== Helper Methods ==============
    
    @staticmethod
    def _wallet_to_response(wallet: DriverWallet) -> WalletResponse:
        """Convert DriverWallet to response schema."""
        return WalletResponse(
            id=str(wallet.id),
            driver_id=wallet.driver_id,
            token_balance=wallet.token_balance,
            total_purchased=wallet.total_purchased,
            total_spent=wallet.total_spent,
            total_bonus=wallet.total_bonus,
            low_balance_threshold=wallet.low_balance_threshold,
            is_low_balance=wallet.is_low_balance,
            is_active=wallet.is_active,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at,
        )
    
    @staticmethod
    def _transaction_to_response(txn: TokenTransaction) -> TransactionResponse:
        """Convert TokenTransaction to response schema."""
        return TransactionResponse(
            id=str(txn.id),
            driver_id=txn.driver_id,
            transaction_type=txn.transaction_type,
            amount=txn.amount,
            balance_after=txn.balance_after,
            payment_reference=txn.payment_reference,
            payment_amount_etb=txn.payment_amount_etb,
            trip_id=txn.trip_id,
            booking_count=txn.booking_count,
            description=txn.description,
            created_at=txn.created_at,
        )
    
    @staticmethod
    def _package_to_response(pkg: TokenPackage) -> PackageResponse:
        """Convert TokenPackage to response schema."""
        return PackageResponse(
            id=str(pkg.id),
            name=pkg.name,
            description=pkg.description,
            tokens=pkg.tokens,
            bonus_tokens=pkg.bonus_tokens,
            total_tokens=pkg.total_tokens,
            price_etb=pkg.price_etb,
            price_per_token=pkg.price_per_token,
            is_active=pkg.is_active,
        )
