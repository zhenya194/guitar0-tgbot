import aiohttp

lessons_api_url: str = "https://api.guitar0.net/api/v1/lessons/"
chords_api_url: str = "https://api.guitar0.net/api/v1/chords/"

async def get_api_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(lessons_api_url, timeout=30) as response:
            data_lessons = await response.json()
        async with session.get(chords_api_url, timeout=30) as response:
            data_chords = await response.json()
    all_data: list = [data_lessons, data_chords]
    return all_data
