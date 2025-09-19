from typing import List, Optional, Dict
from app.infrastructure.repositories.listing_price_list_repository import ListingPriceListRepository
from app.api.v1.schemas.guesty_schema import ListingPriceListMapping, CreateListingMappingRequest, UpdateListingMappingRequest


class ListingPriceListService:
    """
    Service for managing Guesty listing to Booking Experts price list mappings.
    """

    def __init__(self, repository: ListingPriceListRepository):
        self.repository = repository

    async def create_mapping(
        self, 
        guesty_listing_id: str, 
        booking_experts_price_list_id: str
    ) -> ListingPriceListMapping:
        """
        Create a new listing to price list mapping.
        """
        mapping_id = await self.repository.create_mapping(
            guesty_listing_id, 
            booking_experts_price_list_id
        )
        
        # Fetch the created mapping
        mapping = await self.repository.get_mapping(guesty_listing_id)
        return ListingPriceListMapping(
            id=mapping["id"],
            guesty_listing_id=mapping["guesty_listing_id"],
            booking_experts_price_list_id=mapping["booking_experts_price_list_id"],
            is_active=bool(mapping["is_active"]),
            created_at=mapping["created_at"],
            updated_at=mapping["updated_at"]
        )

    async def get_mapping(self, guesty_listing_id: str) -> Optional[ListingPriceListMapping]:
        """
        Get the price list mapping for a specific Guesty listing ID.
        """
        mapping = await self.repository.get_mapping(guesty_listing_id)
        if not mapping:
            return None
        
        return ListingPriceListMapping(
            id=mapping["id"],
            guesty_listing_id=mapping["guesty_listing_id"],
            booking_experts_price_list_id=mapping["booking_experts_price_list_id"],
            is_active=bool(mapping["is_active"]),
            created_at=mapping["created_at"],
            updated_at=mapping["updated_at"]
        )

    async def get_all_mappings(self, active_only: bool = True) -> List[ListingPriceListMapping]:
        """
        Get all listing to price list mappings.
        """
        mappings = await self.repository.get_all_mappings(active_only)
        return [
            ListingPriceListMapping(
                id=mapping["id"],
                guesty_listing_id=mapping["guesty_listing_id"],
                booking_experts_price_list_id=mapping["booking_experts_price_list_id"],
                is_active=bool(mapping["is_active"]),
                created_at=mapping["created_at"],
                updated_at=mapping["updated_at"]
            )
            for mapping in mappings
        ]

    async def update_mapping(
        self, 
        guesty_listing_id: str, 
        booking_experts_price_list_id: str
    ) -> Optional[ListingPriceListMapping]:
        """
        Update the price list for a specific Guesty listing ID.
        """
        updated = await self.repository.update_mapping(
            guesty_listing_id, 
            booking_experts_price_list_id
        )
        
        if not updated:
            return None
            
        return await self.get_mapping(guesty_listing_id)

    async def deactivate_mapping(self, guesty_listing_id: str) -> bool:
        """
        Deactivate a listing to price list mapping.
        """
        return await self.repository.deactivate_mapping(guesty_listing_id)

    async def get_price_list_for_listing(self, guesty_listing_id: str) -> Optional[str]:
        """
        Get the Booking Experts price list ID for a Guesty listing.
        """
        return await self.repository.get_price_list_for_listing(guesty_listing_id)

    async def get_listings_for_price_list(self, booking_experts_price_list_id: str) -> List[str]:
        """
        Get all Guesty listing IDs that are mapped to a specific price list.
        """
        return await self.repository.get_listings_for_price_list(booking_experts_price_list_id)

    async def bulk_create_mappings(self, mappings: List[CreateListingMappingRequest]) -> int:
        """
        Create multiple mappings in a single transaction.
        """
        mapping_data = [
            {
                "guesty_listing_id": mapping.guesty_listing_id,
                "booking_experts_price_list_id": mapping.booking_experts_price_list_id
            }
            for mapping in mappings
        ]
        return await self.repository.bulk_create_mappings(mapping_data)
