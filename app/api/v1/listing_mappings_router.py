from typing import List, Dict
from fastapi import APIRouter, HTTPException, Depends
from api.v1.schemas.guesty_schema import (
    ListingPriceListMapping, 
    CreateListingMappingRequest, 
    UpdateListingMappingRequest
)
from app.shared.dependencies import get_listing_price_list_service
from app.application.listing_price_list_service import ListingPriceListService

router = APIRouter()

@router.post("/", response_model=ListingPriceListMapping)
async def create_listing_mapping(
    request: CreateListingMappingRequest,
    service: ListingPriceListService = Depends(get_listing_price_list_service),
):
    """
    Create a new mapping between a Guesty listing and a Booking Experts price list.
    """
    try:
        return await service.create_mapping(
            request.guesty_listing_id,
            request.booking_experts_price_list_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create mapping: {str(e)}")

@router.get("/", response_model=List[ListingPriceListMapping])
async def get_all_listing_mappings(
    active_only: bool = True,
    service: ListingPriceListService = Depends(get_listing_price_list_service),
):
    """
    Get all listing to price list mappings.
    """
    return await service.get_all_mappings(active_only)

@router.get("/{guesty_listing_id}", response_model=ListingPriceListMapping)
async def get_listing_mapping(
    guesty_listing_id: str,
    service: ListingPriceListService = Depends(get_listing_price_list_service),
):
    """
    Get the price list mapping for a specific Guesty listing ID.
    """
    mapping = await service.get_mapping(guesty_listing_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping

@router.put("/{guesty_listing_id}", response_model=ListingPriceListMapping)
async def update_listing_mapping(
    guesty_listing_id: str,
    request: UpdateListingMappingRequest,
    service: ListingPriceListService = Depends(get_listing_price_list_service),
):
    """
    Update the price list for a specific Guesty listing ID.
    """
    mapping = await service.update_mapping(
        guesty_listing_id,
        request.booking_experts_price_list_id
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping

@router.delete("/{guesty_listing_id}")
async def deactivate_listing_mapping(
    guesty_listing_id: str,
    service: ListingPriceListService = Depends(get_listing_price_list_service),
):
    """
    Deactivate a listing to price list mapping.
    """
    success = await service.deactivate_mapping(guesty_listing_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"message": "Mapping deactivated successfully"}

@router.post("/bulk", response_model=Dict[str, int])
async def bulk_create_listing_mappings(
    requests: List[CreateListingMappingRequest],
    service: ListingPriceListService = Depends(get_listing_price_list_service),
):
    """
    Create multiple listing to price list mappings in a single transaction.
    """
    try:
        count = await service.bulk_create_mappings(requests)
        return {"created_count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create mappings: {str(e)}")
