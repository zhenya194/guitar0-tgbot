import aiofiles
import aiohttp
import json

lessons_api_url: str = "https://api.guitar0.net/api/v1/lessons/"
chords_api_url: str = "https://api.guitar0.net/api/v1/chords/"

async def get_api_data():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(lessons_api_url, timeout=30) as response:
                data_lessons = await response.json()
                async with aiofiles.open("db/api/lessons.json", "w", encoding="utf-8") as file:
                    json_text = json.dumps(data_lessons, ensure_ascii=False, indent=4)
                    await file.write(json_text)
        except:
            async with aiofiles.open("db/api/lessons.json", "r", encoding="utf-8") as file:
                data_lessons = file
        try:
            async with session.get(chords_api_url, timeout=30) as response:
                data_chords = await response.json()
                async with aiofiles.open("db/api/chords.json", "w", encoding="utf-8") as file:
                    json_text = json.dumps(data_chords, ensure_ascii=False, indent=4)
                    await file.write(json_text)
        except:
            async with aiofiles.open("db/api/chords.json", "r", encoding="utf-8") as file:
                data_chords = file
    all_data: list = [data_lessons, data_chords]
    return all_data
