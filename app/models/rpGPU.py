from . import *
from .gpu import GPU
from .rps import RPS

class RpGPU(BaseModel):
    id = PrimaryKeyField()
    rp = ForeignKeyField(RPS)
    gpu = ForeignKeyField(GPU, backref="rp_with_GPU")
    gpu_memory = IntegerField(default="")
    suitability = IntegerField(default=2)

