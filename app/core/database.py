from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client for database operations."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance with sanitized credentials."""
        if cls._instance is None:
            # Очищаем URL и Key от случайных пробелов, переносов строк и кавычек
            url = str(settings.SUPABASE_URL or "").strip().strip("'\"")
            key = str(settings.SUPABASE_KEY or "").strip().strip("'\"")
            
            if not url or not key:
                logger.error("SUPABASE_URL or SUPABASE_KEY is empty in settings!")
                raise ValueError("Supabase credentials are missing")

            key_preview = f"{key[:8]}...{key[-6:]}" if len(key) > 14 else "INVALID_LENGTH"
            logger.info(f"Initializing Supabase client with URL: {url}, Key preview: {key_preview}")
            
            cls._instance = create_client(url, key)
            logger.info("Supabase client initialized successfully")
        return cls._instance

    @classmethod
    async def insert_mechanic_audit(
        cls,
        brand_name: str,
        scenario: str,
        mechanic_id: int,
        mechanic_name: str,
        screenshot_url: str,
        page_url: str,
        metadata: Dict[str, Any],
        maturity_level: int,
        ui_quality_score: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Insert a mechanic audit record into the database."""
        client = cls.get_client()
        
        data = {
            "brand_name": brand_name,
            "scenario": scenario,
            "mechanic_id": mechanic_id,
            "mechanic_name": mechanic_name,
            "screenshot_url": screenshot_url,
            "page_url": page_url,
            "metadata": metadata,
            "maturity_level": maturity_level,
            "ui_quality_score": ui_quality_score,
            "notes": notes
        }
        
        try:
            result = client.table("mechanic_audits").insert(data).execute()
            logger.info(f"Inserted mechanic audit for {brand_name} - {mechanic_name}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error inserting mechanic audit: {e}")
            raise

    @classmethod
    async def insert_red_flag(
        cls,
        audit_id: str,
        flag_type: str,
        severity: str,
        description: str,
        recommended_action: str
    ) -> Dict[str, Any]:
        """Insert a red flag record into the database."""
        client = cls.get_client()
        
        data = {
            "audit_id": audit_id,
            "flag_type": flag_type,
            "severity": severity,
            "description": description,
            "recommended_action": recommended_action
        }
        
        try:
            result = client.table("red_flags").insert(data).execute()
            logger.info(f"Inserted red flag: {flag_type} - {description}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error inserting red flag: {e}")
            raise

    @classmethod
    async def get_competitors(cls) -> List[Dict[str, Any]]:
        """Retrieve all competitors from the database."""
        client = cls.get_client()
        
        try:
            result = client.table("competitors").select("*").execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving competitors: {e}")
            raise

    @classmethod
    async def insert_competitor(
        cls,
        name: str,
        website: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Insert a new competitor into the database."""
        client = cls.get_client()
        
        data = {
            "name": name,
            "website": website,
            "notes": notes
        }
        
        try:
            result = client.table("competitors").insert(data).execute()
            logger.info(f"Inserted competitor: {name}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error inserting competitor: {e}")
            raise

    @classmethod
    async def delete_competitor(cls, competitor_id: str) -> bool:
        """Delete a competitor from the database."""
        client = cls.get_client()
        
        try:
            client.table("competitors").delete().eq("id", competitor_id).execute()
            logger.info(f"Deleted competitor: {competitor_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting competitor: {e}")
            raise

    @classmethod
    async def get_mechanic_maturity_levels(
        cls,
        brand_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve maturity levels for mechanics."""
        client = cls.get_client()
        
        try:
            query = client.table("mechanic_maturity").select("*")
            if brand_name:
                query = query.eq("brand_name", brand_name)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving maturity levels: {e}")
            raise

    @classmethod
    async def get_red_flags(
        cls,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve red flags from the database."""
        client = cls.get_client()
        
        try:
            query = client.table("red_flags").select("*").order("created_at", desc=True)
            if severity:
                query = query.eq("severity", severity)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving red flags: {e}")
            raise


# Convenience function
def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return SupabaseClient.get_client()
