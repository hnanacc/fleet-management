from enum import Enum
import json

class Some(str, Enum):
    Role = 'role'

print(json.dumps(Some.Role))

