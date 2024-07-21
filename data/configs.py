import json
import aiofiles

class ConfigLoader:
    def __init__(self, path):
        self.path = path
        with open(path, 'r', encoding='utf-8')as f:
            self.config = json.loads(f.read())
            
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.config, indent=4, ensure_ascii=False))

    async def save_async(self):
        async with aiofiles.open(self.path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.config, indent=4, ensure_ascii=False))
