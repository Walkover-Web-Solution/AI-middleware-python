import asyncio
import json
from src.services.cache_service import demo_key_expiration, client

async def main():
    # Store list value with key
    key = 'file_123'
    value = ['1234', '5678']
    
    # Store the value and set TTL to 10 seconds
    await client.set(key, json.dumps(value), ex=10)
    print(f"Stored key '{key}' with value {value}")
    
    # Get and display the value
    stored_value = await client.get(key)
    if stored_value:
        print(f"Retrieved value: {json.loads(stored_value)}")
    
    # Set up expiration listener
    await demo_key_expiration(key, json.dumps(value), ttl=10)
    
    # Keep the script running to observe the expiration
    print("Waiting for key expiration...")
    await asyncio.sleep(15)  # Wait for 15 seconds to ensure we see the expiration

if __name__ == "__main__":
    asyncio.run(main())
