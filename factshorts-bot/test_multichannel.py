import asyncio
from factshorts.pipeline import generate_and_render

async def test_channels():
    channels = ["horror", "space", "psychology"]
    for channel in channels:
        print(f"Testing channel: {channel}")
        try:
            res = await generate_and_render(niche=channel)
            print(f"Result for {channel}: {res}")
        except Exception as e:
            print(f"Error for {channel}: {e}")

if __name__ == "__main__":
    asyncio.run(test_channels())
