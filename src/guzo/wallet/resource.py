"""Wallet domain resource - API routes for token wallet system."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.guzo.auth.core import User, UserRole
from src.guzo.middleware import get_current_user_required, get_current_admin, get_current_driver
from src.guzo.wallet.core import (
    WalletResponse,
    TransactionResponse,
    PackageResponse,
    FeeConfigResponse,
    PurchaseTokensRequest,
    ManualCreditRequest,
    CreatePackageRequest,
    UpdatePackageRequest,
    UpdateFeeConfigRequest,
    UpdateWalletSettingsRequest,
)
from src.guzo.wallet.service import WalletService, InsufficientTokensError
from src.guzo.core import StatusResponse


router = APIRouter(prefix="/wallet", tags=["Wallet"])


# ============== Response Models ==============

class BalanceCheckResponse(BaseModel):
    """Response for balance check."""
    can_accept: bool
    token_balance: int
    estimated_fee: int
    minimum_required: int
    reason: Optional[str] = None


class TokenStatsResponse(BaseModel):
    """Response for platform token statistics."""
    total_wallets: int
    total_balance_in_circulation: int
    total_tokens_sold: int
    total_tokens_spent: int
    total_bonus_given: int
    low_balance_drivers: int


class TransactionListResponse(BaseModel):
    """Response for paginated transaction list."""
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int


# ============== Driver Endpoints ==============

@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(driver: User = Depends(get_current_driver)):
    """Get current driver's wallet. Creates one if doesn't exist."""
    try:
        wallet = await WalletService.get_or_create_wallet(str(driver.id))
        return WalletService._wallet_to_response(wallet)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me/balance-check", response_model=BalanceCheckResponse)
async def check_my_balance(
    expected_seats: int = Query(default=1, ge=1, le=20),
    driver: User = Depends(get_current_driver),
):
    """Check if driver has enough tokens to accept a trip."""
    result = await WalletService.check_balance_for_trip(
        str(driver.id),
        expected_seats
    )
    return BalanceCheckResponse(**result)


@router.get("/me/transactions", response_model=TransactionListResponse)
async def get_my_transactions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    driver: User = Depends(get_current_driver),
):
    """Get driver's transaction history."""
    transactions = await WalletService.get_transaction_history(
        str(driver.id), limit, offset
    )
    total = await WalletService.get_transaction_count(str(driver.id))
    
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/me/settings", response_model=WalletResponse)
async def update_my_wallet_settings(
    settings: UpdateWalletSettingsRequest,
    driver: User = Depends(get_current_driver),
):
    """Update driver's wallet settings (e.g., low balance threshold)."""
    wallet = await WalletService.update_wallet_settings(
        str(driver.id),
        settings.low_balance_threshold
    )
    return WalletService._wallet_to_response(wallet)


# ============== Public Endpoints ==============

@router.get("/packages", response_model=list[PackageResponse])
async def get_token_packages():
    """Get all available token packages."""
    return await WalletService.get_available_packages()


@router.get("/fee-config", response_model=FeeConfigResponse)
async def get_fee_configuration():
    """Get current platform fee configuration."""
    return await WalletService.get_fee_config()


# ============== Admin Endpoints - Token Sales ==============

@router.post("/admin/sell-tokens", response_model=TransactionResponse)
async def sell_tokens_to_driver(
    request: PurchaseTokensRequest,
    admin: User = Depends(get_current_admin),
):
    """
    Admin sells tokens to a driver.
    
    The admin should verify payment (cash, bank transfer, etc.) before
    calling this endpoint to credit tokens to the driver's wallet.
    """
    try:
        transaction = await WalletService.sell_tokens(
            driver_id=request.driver_id,
            package_id=request.package_id,
            payment_reference=request.payment_reference,
            admin_id=str(admin.id),
            notes=request.notes,
        )
        return WalletService._transaction_to_response(transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/credit", response_model=TransactionResponse)
async def credit_tokens(
    request: ManualCreditRequest,
    admin: User = Depends(get_current_admin),
):
    """
    Admin manually credits or debits tokens to/from a driver.
    
    Use positive amount to credit, negative to debit.
    """
    try:
        transaction = await WalletService.manual_adjustment(
            driver_id=request.driver_id,
            amount=request.amount,
            description=request.description,
            admin_id=str(admin.id),
            notes=request.notes,
        )
        return WalletService._transaction_to_response(transaction)
    except InsufficientTokensError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient tokens: need {e.required}, have {e.available}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Admin Endpoints - Wallet Management ==============

@router.get("/admin/driver/{driver_id}", response_model=WalletResponse)
async def get_driver_wallet(
    driver_id: str,
    admin: User = Depends(get_current_admin),
):
    """Admin gets a specific driver's wallet."""
    wallet = await WalletService.get_wallet_response(driver_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.get("/admin/driver/{driver_id}/transactions", response_model=TransactionListResponse)
async def get_driver_transactions(
    driver_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(get_current_admin),
):
    """Admin gets a driver's transaction history."""
    transactions = await WalletService.get_transaction_history(
        driver_id, limit, offset
    )
    total = await WalletService.get_transaction_count(driver_id)
    
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/admin/recent-purchases", response_model=list[TransactionResponse])
async def get_recent_purchases(
    limit: int = Query(default=50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
):
    """Get recent token purchases across all drivers."""
    return await WalletService.get_recent_purchases(limit)


@router.get("/admin/low-balance", response_model=list[WalletResponse])
async def get_low_balance_drivers(
    admin: User = Depends(get_current_admin),
):
    """Get drivers with low token balance."""
    return await WalletService.get_low_balance_drivers()


@router.get("/admin/stats", response_model=TokenStatsResponse)
async def get_token_statistics(
    admin: User = Depends(get_current_admin),
):
    """Get platform-wide token statistics."""
    stats = await WalletService.get_platform_token_stats()
    return TokenStatsResponse(**stats)


# ============== Admin Endpoints - Package Management ==============

@router.post("/admin/packages", response_model=PackageResponse)
async def create_package(
    data: CreatePackageRequest,
    admin: User = Depends(get_current_admin),
):
    """Create a new token package."""
    try:
        package = await WalletService.create_package(data)
        return WalletService._package_to_response(package)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/admin/packages/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: str,
    data: UpdatePackageRequest,
    admin: User = Depends(get_current_admin),
):
    """Update a token package."""
    try:
        package = await WalletService.update_package(package_id, data)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        return WalletService._package_to_response(package)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/admin/packages/{package_id}", response_model=StatusResponse)
async def delete_package(
    package_id: str,
    admin: User = Depends(get_current_admin),
):
    """Delete a token package."""
    success = await WalletService.delete_package(package_id)
    if not success:
        raise HTTPException(status_code=404, detail="Package not found")
    return StatusResponse(status="success", message="Package deleted")


# ============== Admin Endpoints - Fee Configuration ==============

@router.patch("/admin/fee-config", response_model=FeeConfigResponse)
async def update_fee_configuration(
    data: UpdateFeeConfigRequest,
    admin: User = Depends(get_current_admin),
):
    """Update platform fee configuration."""
    config = await WalletService.update_fee_config(data)
    return FeeConfigResponse(
        fee_per_seat=config.fee_per_seat,
        fee_per_trip=config.fee_per_trip,
        minimum_balance_required=config.minimum_balance_required,
    )
