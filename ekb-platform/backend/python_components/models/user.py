import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Text, UniqueConstraint # Import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db.session import Base # Assuming python_components is in sys.path

# Association table for User and Role (Many-to-Many)
user_roles_table = Table('user_roles', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.user_id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.role_id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=True) # Nullable if using SSO exclusively for some users
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # Nullable if using SSO exclusively
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean(), default=True)
    sso_provider = Column(String, nullable=True)
    sso_subject_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    roles = relationship("Role", secondary=user_roles_table, back_populates="users")

    # Add a check constraint for authentication method if possible through SQLAlchemy,
    # otherwise rely on the DB schema's check constraint.
    # __table_args__ = (
    #     CheckConstraint(
    #         "(username IS NOT NULL AND hashed_password IS NOT NULL AND sso_provider IS NULL AND sso_subject_id IS NULL) OR "
    #         "(username IS NULL AND hashed_password IS NULL AND sso_provider IS NOT NULL AND sso_subject_id IS NOT NULL) OR "
    #         "(email IS NOT NULL)",
    #         name="chk_auth_method"
    #     ),
    # )
    __table_args__ = (
        UniqueConstraint('sso_provider', 'sso_subject_id', name='uq_sso_provider_subject'),
        # Potentially add other table args like the CheckConstraint here if not handled by DB schema directly
    )


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users = relationship("User", secondary=user_roles_table, back_populates="roles")


# Placeholder models for Spaces and Permissions if needed later, to match the schema
# class Permission(Base):
#     __tablename__ = "permissions"
#     permission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     permission_name = Column(String, unique=True, nullable=False)
#     description = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# class Space(Base):
#     __tablename__ = "spaces"
#     space_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     space_name = Column(String, nullable=False)
#     space_type = Column(String, nullable=False)
#     description = Column(Text, nullable=True)
#     created_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False) # Or SET NULL
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

#     creator = relationship("User")

# user_space_roles_table = Table('user_space_roles', Base.metadata,
#     Column('user_id', UUID(as_uuid=True), ForeignKey('users.user_id'), primary_key=True),
#     Column('space_id', UUID(as_uuid=True), ForeignKey('spaces.space_id'), primary_key=True),
#     Column('role_id', UUID(as_uuid=True), ForeignKey('roles.role_id'), primary_key=True),
#     Column('created_at', DateTime(timezone=True), server_default=func.now())
# )

# Role.spaces = relationship("Space", secondary=user_space_roles_table, viewonly=True) # Or define specific backpop
# User.spaces = relationship("Space", secondary=user_space_roles_table, viewonly=True) # Or define specific backpop
# Space.members = relationship("User", secondary=user_space_roles_table, viewonly=True)
# Space.roles = relationship("Role", secondary=user_space_roles_table, viewonly=True)
