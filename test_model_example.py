#!/usr/bin/env python3
"""
Example model to test BaseModel functionality
"""

import sys
sys.path.append('backend')

from sqlalchemy import Column, String
from db.base import BaseModel

class ExampleModel(BaseModel):
    __tablename__ = "example_models"
    
    name = Column(String(255), nullable=False)
    description = Column(String(500))

# Test the model
if __name__ == "__main__":
    print("✅ Example model created successfully!")
    print(f"Table name: {ExampleModel.__tablename__}")
    print(f"Columns: {[col.name for col in ExampleModel.__table__.columns]}")
    print(f"Has UUID id: {'id' in [col.name for col in ExampleModel.__table__.columns]}")
    print(f"Has timestamps: {'created_at' in [col.name for col in ExampleModel.__table__.columns] and 'updated_at' in [col.name for col in ExampleModel.__table__.columns]}") 