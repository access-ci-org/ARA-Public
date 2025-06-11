from . import *

class GPU(BaseModel):
    id = PrimaryKeyField()
    gpu_name = CharField(max_length=40, unique=True, constraints=[SQL('COLLATE NOCASE')])
