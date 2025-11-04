# Enable RLS on riders table

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("riders", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on riders_riderprofile table
                ALTER TABLE riders_riderprofile ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to rider profiles" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Riders can view own profile" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Riders can update own profile" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Warehouse managers can view riders" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Staff can manage all rider profiles" ON riders_riderprofile;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to rider profiles"
                ON riders_riderprofile
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Riders can view their own profile
                CREATE POLICY "Riders can view own profile"
                ON riders_riderprofile
                FOR SELECT
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Riders can update their own profile
                CREATE POLICY "Riders can update own profile"
                ON riders_riderprofile
                FOR UPDATE
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
                
                -- Policy: Warehouse managers can view riders assigned to their warehouse
                CREATE POLICY "Warehouse managers can view riders"
                ON riders_riderprofile
                FOR SELECT
                TO authenticated
                USING (
                    warehouse_id IN (
                        SELECT id FROM warehouses_warehouse 
                        WHERE admin_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                    OR
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND role = 'WAREHOUSE_MANAGER'
                    )
                );
                
                -- Policy: Staff can manage all rider profiles
                CREATE POLICY "Staff can manage all rider profiles"
                ON riders_riderprofile
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
                DROP POLICY IF EXISTS "Service role has full access to rider profiles" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Riders can view own profile" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Riders can update own profile" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Warehouse managers can view riders" ON riders_riderprofile;
                DROP POLICY IF EXISTS "Staff can manage all rider profiles" ON riders_riderprofile;
                ALTER TABLE riders_riderprofile DISABLE ROW LEVEL SECURITY;
            """,
        ),
    ]
