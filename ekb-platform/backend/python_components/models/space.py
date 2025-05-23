import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .user import User # Import User model for relationships
from db.session import Base # Assuming python_components is in sys.path

# Association table for User, Space, and Role (Many-to-Many-to-Many through UserSpaceRole)
# This table directly links users to spaces with a specific role.
user_space_roles_table = Table('user_space_roles', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"), primary_key=True),
    Column('space_id', UUID(as_uuid=True), ForeignKey('spaces.space_id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.role_id', ondelete="CASCADE"), primary_key=True), # Assuming roles are global and contextually applied
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class Space(Base):
    __tablename__ = "spaces"

    space_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_name = Column(String, nullable=False)
    space_type = Column(String, nullable=False) # e.g., 'group', 'team', 'project'
    description = Column(Text, nullable=True)
    
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="SET NULL"), nullable=True) # Allow space to exist if creator is deleted
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to the user who created the space
    creator = relationship("User") # This assumes User model is defined and accessible

    # Relationship to users and their roles within this space
    # This provides a way to see all UserSpaceRole entries for a space
    user_roles_in_space = relationship("UserSpaceRole", back_populates="space", cascade="all, delete-orphan")


class UserSpaceRole(Base):
    # This class maps to the user_space_roles_table defined above.
    # It should not redefine __tablename__ or columns if __table__ is used.
    __table__ = user_space_roles_table

    # Relationships to easily access User, Space, Role from a UserSpaceRole instance
    # The columns (user_id, space_id, role_id, created_at) are defined in user_space_roles_table.
    # SQLAlchemy will map them automatically.
    
    # Ensure corresponding back_populates are defined in User and Role models
    user = relationship("User", backref="space_role_associations") 
    space = relationship("Space", back_populates="user_roles_in_space")
    role = relationship("Role", backref="space_role_associations")

# Comments from the previous erroneous version, now correctly formatted:
# The UserSpaceRole model is explicitly bound to the user_space_roles_table. I've also added comments regarding necessary relationships
# that would need to be added to User and Role models in models/user.py for full ORM integration (e.g., User.space_links).
# For now, the Space.user_roles_in_space relationship is defined.

# Next, I'll create schemas/space.py (or add to schemas.py) for Pydantic schemas related to spaces.
# I'll create a new file schemas/space.py for better organization.

# Add to models/__init__.py:
# from .space import Space, UserSpaceRole

# Update User model in models/user.py to include relationship to UserSpaceRole:
# class User(Base):
#   ...
#   # space_links = relationship("UserSpaceRole", back_populates="user") # Or use the backref defined above
#   # This allows: user_obj.space_links to get a list of UserSpaceRole objects for that user.
#   # From there, you can get space and role for each link.

# Update Role model in models/user.py:
# class Role(Base):
#   ...
#   # in_space_links = relationship("UserSpaceRole", back_populates="role") # Or use the backref defined above

# The relationship in Space model:
# user_roles_in_space = relationship("UserSpaceRole", back_populates="space", cascade="all, delete-orphan")
# This is consistent.

# The current User.roles relationship is for global roles. We need to distinguish.
# The `user_roles_table` is for global roles. `user_space_roles_table` is for space-specific roles.
# This is clear.

# So, the models are:
# User <-> Role (global, ManyToMany via user_roles_table)
# User <-> UserSpaceRole <-> Space (User has roles in Spaces)
# Role <-> UserSpaceRole (Role is used in Spaces)
# This structure is fine.
