# components/forms.py
from pydantic import BaseModel, Field

# This is the corrected data model.
# The ```` has been removed from the last line.
class StaffModel(BaseModel):
    username: str = Field(..., min_length=3)
    # When editing, we'll handle the password field separately in the form logic
    password: str | None = Field(None, min_length=6, description="Leave blank to keep unchanged when editing.")
    full_name: str = Field(..., min_length=3)
    role: str
    assigned_city: str | None = None
    assigned_ucs: list[str] | None = None
    is_active: bool = True