# Generated migration to enable RLS on users_user_permissions table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_shopkeeperprofile_shop_address_and_more'),
    ]

    operations = [
        # Enable RLS on users_user_permissions table
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on users_user_permissions table
                ALTER TABLE users_user_permissions ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist (for idempotency)
                DROP POLICY IF EXISTS "Users can view their own permissions" ON users_user_permissions;
                DROP POLICY IF EXISTS "Admins can manage all permissions" ON users_user_permissions;
                DROP POLICY IF EXISTS "Service role has full access to permissions" ON users_user_permissions;
                
                -- Policy: Service role (backend) has full access
                CREATE POLICY "Service role has full access to permissions"
                ON users_user_permissions
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view their own permissions
                CREATE POLICY "Users can view their own permissions" 
                ON users_user_permissions
                FOR SELECT
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users 
                        WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Only admins/staff can manage permissions
                CREATE POLICY "Admins can manage all permissions"
                ON users_user_permissions
                FOR ALL
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true)
                    )
                )
                WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true)
                    )
                );
            """,
            reverse_sql="""
                -- Disable Row Level Security on users_user_permissions table
                DROP POLICY IF EXISTS "Users can view their own permissions" ON users_user_permissions;
                DROP POLICY IF EXISTS "Admins can manage all permissions" ON users_user_permissions;
                DROP POLICY IF EXISTS "Service role has full access to permissions" ON users_user_permissions;
                ALTER TABLE users_user_permissions DISABLE ROW LEVEL SECURITY;
            """
        ),

        # Enable RLS on users_groups table (another Django PermissionsMixin table)
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on users_groups table
                ALTER TABLE users_groups ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist (for idempotency)
                DROP POLICY IF EXISTS "Users can view their own groups" ON users_groups;
                DROP POLICY IF EXISTS "Admins can manage all groups" ON users_groups;
                DROP POLICY IF EXISTS "Service role has full access to groups" ON users_groups;
                
                -- Policy: Service role (backend) has full access
                CREATE POLICY "Service role has full access to groups"
                ON users_groups
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view their own groups
                CREATE POLICY "Users can view their own groups" 
                ON users_groups
                FOR SELECT
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users 
                        WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Only admins/staff can manage groups
                CREATE POLICY "Admins can manage all groups"
                ON users_groups
                FOR ALL
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true)
                    )
                )
                WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true)
                    )
                );
            """,
            reverse_sql="""
                -- Disable Row Level Security on users_groups table
                DROP POLICY IF EXISTS "Users can view their own groups" ON users_groups;
                DROP POLICY IF EXISTS "Admins can manage all groups" ON users_groups;
                DROP POLICY IF EXISTS "Service role has full access to groups" ON users_groups;
                ALTER TABLE users_groups DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]

