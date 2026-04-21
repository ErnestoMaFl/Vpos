from app.services.search_service import search_service
import asyncio
import json

async def test_search():
    query = "coca"
    print(f"Searching for: {query}")
    
    result = await search_service.search_product(query)
    print("Result:")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_search())
