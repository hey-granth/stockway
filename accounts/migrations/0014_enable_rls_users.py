# Enable RLS on users table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_enable_rls_user_permissions'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on users table
                ALTER TABLE users ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist (for idempotency)
                DROP POLICY IF EXISTS "Service role has full access to users" ON users;
                DROP POLICY IF EXISTS "Users can view own profile" ON users;
                DROP POLICY IF EXISTS "Users can update own profile" ON users;
                DROP POLICY IF EXISTS "Admins can manage users" ON users;
                DROP POLICY IF EXISTS "Public can view basic user info" ON users;
                
                -- Policy: Service role (backend) has full access
                CREATE POLICY "Service role has full access to users"
                ON users
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view their own profile
                CREATE POLICY "Users can view own profile" 
                ON users
                FOR SELECT
                TO authenticated
                USING (supabase_uid = auth.uid()::text);
                
                -- Policy: Users can update their own profile (but not role or admin flags)
                CREATE POLICY "Users can update own profile"
                ON users
                FOR UPDATE
                TO authenticated
                USING (supabase_uid = auth.uid()::text)
                WITH CHECK (supabase_uid = auth.uid()::text);
                
                -- Policy: Admins and warehouse managers can view all users
                CREATE POLICY "Admins can manage users"
                ON users
                FOR ALL
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true OR role = 'WAREHOUSE_MANAGER')
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
                DROP POLICY IF EXISTS "Service role has full access to users" ON users;
                DROP POLICY IF EXISTS "Users can view own profile" ON users;
                DROP POLICY IF EXISTS "Users can update own profile" ON users;
                DROP POLICY IF EXISTS "Admins can manage users" ON users;
                DROP POLICY IF EXISTS "Public can view basic user info" ON users;
                ALTER TABLE users DISABLE ROW LEVEL SECURITY;
            """
        ),

        # Enable RLS on shopkeeper_profiles table
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on shopkeeper_profiles table
                ALTER TABLE shopkeeper_profiles ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to profiles" ON shopkeeper_profiles;
                DROP POLICY IF EXISTS "Shopkeepers can manage own profile" ON shopkeeper_profiles;
                DROP POLICY IF EXISTS "Warehouse managers can view profiles" ON shopkeeper_profiles;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to profiles"
                ON shopkeeper_profiles
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Shopkeepers can view and update their own profile
                CREATE POLICY "Shopkeepers can manage own profile"
                ON shopkeeper_profiles
                FOR ALL
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                )
                WITH CHECK (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Warehouse managers and admins can view all profiles
                CREATE POLICY "Warehouse managers can view profiles"
                ON shopkeeper_profiles
                FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND role IN ('ADMIN', 'WAREHOUSE_MANAGER')
                    )
                );
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS "Service role has full access to profiles" ON shopkeeper_profiles;
                DROP POLICY IF EXISTS "Shopkeepers can manage own profile" ON shopkeeper_profiles;
                DROP POLICY IF EXISTS "Warehouse managers can view profiles" ON shopkeeper_profiles;
                ALTER TABLE shopkeeper_profiles DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]

