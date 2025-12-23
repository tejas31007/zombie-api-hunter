from pydantic import BaseModel
from datetime import datetime

class ModelMetadata(BaseModel):
    """
    The 'ID Card' for a machine learning model.
    Stores vital information about the model's origin and performance.
    """
    version: str
    algorithm: str
    trained_at: str
    author: str
    description: str
    
    # Factory method to create a fresh metadata object
    @classmethod
    def create(cls, version: str, algorithm: str, author: str = "Tejas"):
        return cls(
            version=version,
            algorithm=algorithm,
            trained_at=datetime.now().isoformat(),
            author=author,
            description="Zombie API Hunter Security Model"
        )