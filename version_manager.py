import datetime
import json
import os

class VersionManager:
    def __init__(self):
        self.version_file = 'version.json'
        self.load_version()
    def load_version(self):
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r') as f:
                self.version = json.load(f)
        else:
            self.version = {
                'major': 1,
                'minor': 0,
                'patch': 237,
                'last_updated': datetime.date.today().isoformat()
            }
            self.save_version()
    
    def save_version(self):
        with open(self.version_file, 'w') as f:
            json.dump(self.version, f, indent=2)
    
    def bump_version(self, level='patch'):
        """
        level: 'major', 'minor', 'patch'のいずれか
        """
        if level == 'major':
            self.version['major'] += 1
            self.version['minor'] = 0
            self.version['patch'] = 0
        elif level == 'minor':
            self.version['minor'] += 1
            self.version['patch'] = 0
        else:  # patch
            self.version['patch'] += 1
        
        self.version['last_updated'] = datetime.date.today().isoformat()
        self.save_version()