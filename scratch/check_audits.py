import asyncio
import httpx
import json

async def check_audits(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        
        print(f"\n--- Audit Data for {coin_id} ---")
        
        # Search for audit keywords in the full response text
        text = json.dumps(data).lower()
        print(f"CertiK found: {'certik' in text}")
        print(f"Hacken found: {'hacken' in text}")
        print(f"Audit found: {'audit' in text}")
        
        if 'audit' in text:
            # Try to find where it is
            for k, v in data.items():
                if 'audit' in str(v).lower():
                    print(f"Audit found in key: {k}")

if __name__ == "__main__":
    # Test with Chainlink (LINK) and Tether (USDT)
    asyncio.run(check_audits("chainlink"))
    asyncio.run(check_audits("tether"))
