-- User Management Schema for EKB Platform (PostgreSQL)

-- Enable UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table: Stores user account information, supporting both local and SSO authentication.
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE,
    hashed_password TEXT,
    email TEXT UNIQUE NOT NULL,
    sso_provider TEXT,
    sso_subject_id TEXT,
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_sso_provider_subject UNIQUE (sso_provider, sso_subject_id),
    CONSTRAINT chk_auth_method CHECK (
        (username IS NOT NULL AND hashed_password IS NOT NULL AND sso_provider IS NULL AND sso_subject_id IS NULL) OR
        (username IS NULL AND hashed_password IS NULL AND sso_provider IS NOT NULL AND sso_subject_id IS NOT NULL) OR
        (email IS NOT NULL) -- Allows for email-only accounts that can be linked or have password set later
        -- This check might need refinement to better handle transitions between local and SSO,
        -- or for users who have both (e.g. SSO linked, but also a local password as backup).
        -- For now, it enforces that EITHER local creds OR SSO creds are set, or just email.
    )
);

COMMENT ON TABLE users IS 'Stores user account information, supporting both local and SSO authentication.';
COMMENT ON COLUMN users.user_id IS 'Primary Key, auto-generated UUID.';
COMMENT ON COLUMN users.username IS 'Unique username for local accounts.';
COMMENT ON COLUMN users.hashed_password IS 'Hashed password for local accounts.';
COMMENT ON COLUMN users.email IS 'Unique email address, used for local accounts and SSO linking.';
COMMENT ON COLUMN users.sso_provider IS 'SSO provider identifier (e.g., ''oidc'', ''saml'').';
COMMENT ON COLUMN users.sso_subject_id IS 'Unique subject identifier from the SSO provider.';
COMMENT ON COLUMN users.full_name IS 'User''s full name.';
COMMENT ON COLUMN users.is_active IS 'Flag indicating if the user account is active (default true).';
COMMENT ON COLUMN users.created_at IS 'Timestamp of when the user account was created (auto-generated).';
COMMENT ON COLUMN users.updated_at IS 'Timestamp of when the user account was last updated (auto-generated).';
COMMENT ON CONSTRAINT uq_sso_provider_subject ON users IS 'Ensures that the combination of SSO provider and subject ID is unique.';
COMMENT ON CONSTRAINT chk_auth_method ON users IS 'Ensures that authentication method details are consistent (local vs. SSO or email-only).';

-- Roles Table: Defines different roles within the system.
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE roles IS 'Defines different roles within the system (e.g., admin, editor, viewer).';
COMMENT ON COLUMN roles.role_id IS 'Primary Key, auto-generated UUID.';
COMMENT ON COLUMN roles.role_name IS 'Unique name of the role (e.g., ''admin'', ''editor'').';
COMMENT ON COLUMN roles.description IS 'Optional description of the role.';
COMMENT ON COLUMN roles.created_at IS 'Timestamp of when the role was created (auto-generated).';
COMMENT ON COLUMN roles.updated_at IS 'Timestamp of when the role was last updated (auto-generated).';

-- UserRoles Junction Table: Assigns roles to users (Many-to-Many).
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE user_roles IS 'Junction table mapping users to global roles (Many-to-Many).';
COMMENT ON COLUMN user_roles.user_id IS 'Foreign Key referencing the Users table.';
COMMENT ON COLUMN user_roles.role_id IS 'Foreign Key referencing the Roles table.';
COMMENT ON COLUMN user_roles.created_at IS 'Timestamp of when the role was assigned to the user (auto-generated).';

-- Permissions Table: Defines specific actions or capabilities within the system.
-- (Optional for now, but good to define for future fine-grained access control)
CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE permissions IS 'Defines specific actions or capabilities (e.g., ''create_document'', ''delete_user'').';
COMMENT ON COLUMN permissions.permission_id IS 'Primary Key, auto-generated UUID.';
COMMENT ON COLUMN permissions.permission_name IS 'Unique name of the permission (e.g., ''create_document'').';
COMMENT ON COLUMN permissions.description IS 'Optional description of the permission.';
COMMENT ON COLUMN permissions.created_at IS 'Timestamp of when the permission was created (auto-generated).';
COMMENT ON COLUMN permissions.updated_at IS 'Timestamp of when the permission was last updated (auto-generated).';

-- RolePermissions Junction Table: Assigns permissions to roles (Many-to-Many).
-- (Optional for now, aligns with the Permissions table)
CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE role_permissions IS 'Junction table mapping permissions to roles (Many-to-Many).';
COMMENT ON COLUMN role_permissions.role_id IS 'Foreign Key referencing the Roles table.';
COMMENT ON COLUMN role_permissions.permission_id IS 'Foreign Key referencing the Permissions table.';
COMMENT ON COLUMN role_permissions.created_at IS 'Timestamp of when the permission was assigned to the role (auto-generated).';

-- Spaces Table: Represents groups, teams, or projects.
CREATE TABLE spaces (
    space_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    space_name TEXT NOT NULL,
    space_type TEXT NOT NULL, -- e.g., 'group', 'team', 'project'
    description TEXT,
    created_by_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE SET NULL, -- Or ON DELETE RESTRICT based on policy
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE spaces IS 'Represents logical spaces like groups, teams, or projects.';
COMMENT ON COLUMN spaces.space_id IS 'Primary Key, auto-generated UUID.';
COMMENT ON COLUMN spaces.space_name IS 'Name of the space.';
COMMENT ON COLUMN spaces.space_type IS 'Type of the space (e.g., ''group'', ''team'', ''project'').';
COMMENT ON COLUMN spaces.description IS 'Optional description of the space.';
COMMENT ON COLUMN spaces.created_by_user_id IS 'Foreign Key referencing the user who created the space.';
COMMENT ON COLUMN spaces.created_at IS 'Timestamp of when the space was created (auto-generated).';
COMMENT ON COLUMN spaces.updated_at IS 'Timestamp of when the space was last updated (auto-generated).';

-- UserSpaceRoles Junction Table: Assigns users roles within a specific space.
CREATE TABLE user_space_roles (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    space_id UUID NOT NULL REFERENCES spaces(space_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE, -- Role specific to the context of the space
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, space_id, role_id)
);

COMMENT ON TABLE user_space_roles IS 'Assigns users roles within a specific space (e.g., user X is admin of space Y).';
COMMENT ON COLUMN user_space_roles.user_id IS 'Foreign Key referencing the Users table.';
COMMENT ON COLUMN user_space_roles.space_id IS 'Foreign Key referencing the Spaces table.';
COMMENT ON COLUMN user_space_roles.role_id IS 'Foreign Key referencing the Roles table (for space-specific roles).';
COMMENT ON COLUMN user_space_roles.created_at IS 'Timestamp of when the space role was assigned to the user (auto-generated).';

-- Triggers to automatically update 'updated_at' timestamps

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at
BEFORE UPDATE ON roles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permissions_updated_at
BEFORE UPDATE ON permissions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spaces_updated_at
BEFORE UPDATE ON spaces
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- End of User Management Schema
