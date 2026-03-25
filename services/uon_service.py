import logging
import aiohttp
from config import UON_API_KEY, UON_BASE_URL

logger = logging.getLogger(__name__)

class UonService:
    @staticmethod
    async def get_user_destination(uon_id: str) -> str:
        """Запрашивает страну назначения из U-ON API (User → Request fallback)."""
        if not UON_API_KEY or UON_API_KEY == "YOUR_UON_API_KEY_HERE":
            logger.warning("UON_API_KEY is not set or is default. Using mock behavior.")
            if uon_id.strip() == "123":
                return "Egypt"
            elif uon_id.strip().isdigit():
                return "Turkey"
            return None
            
        async with aiohttp.ClientSession() as session:
            try:
                # Попытка как User
                url_user = f"{UON_BASE_URL.rstrip('/')}/{UON_API_KEY}/user/{uon_id}.json"
                async with session.get(url_user) as response:
                    if response.status == 200:
                        data = await response.json()
                        users = data.get('user', [])
                        if users and len(users) > 0:
                            reqs = users[0].get('requests', [])
                            if reqs:
                                country = reqs[0].get('country') or reqs[0].get('country_name')
                                if country:
                                    return country
                            country = users[0].get('country') or users[0].get('country_name')
                            if country:
                                return country
                                
                # Fallback: попытка как Request
                url = f"{UON_BASE_URL.rstrip('/')}/{UON_API_KEY}/request/{uon_id}.json"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        requests = data.get('request', data.get('requests', []))
                        if requests and len(requests) > 0:
                            country = requests[0].get('country') or requests[0].get('country_name')
                            if country:
                                return country
                                
            except Exception as e:
                logger.error(f"Error fetching from U-ON API: {e}")
                
        return None
