# Enable RLS on warehouses table

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("warehouses", "0003_warehouse_location_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on warehouses_warehouse table
                ALTER TABLE warehouses_warehouse ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to warehouses" ON warehouses_warehouse;
                DROP POLICY IF EXISTS "Public can view warehouses" ON warehouses_warehouse;
                DROP POLICY IF EXISTS "Warehouse admins can manage own warehouse" ON warehouses_warehouse;
                DROP POLICY IF EXISTS "Staff can manage all warehouses" ON warehouses_warehouse;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to warehouses"
                ON warehouses_warehouse
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: All authenticated users can view warehouses (for finding nearest warehouse)
                CREATE POLICY "Public can view warehouses"
                ON warehouses_warehouse
                FOR SELECT
                TO authenticated
                USING (true);
                
                -- Policy: Warehouse admins can manage their own warehouse
                CREATE POLICY "Warehouse admins can manage own warehouse"
                ON warehouses_warehouse
                FOR ALL
                TO authenticated
                USING (
                    admin_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                )
                WITH CHECK (
                    admin_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Staff can manage all warehouses
                CREATE POLICY "Staff can manage all warehouses"
                ON warehouses_warehouse
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
                DROP POLICY IF EXISTS "Service role has full access to warehouses" ON warehouses_warehouse;
                DROP POLICY IF EXISTS "Public can view warehouses" ON warehouses_warehouse;
                DROP POLICY IF EXISTS "Warehouse admins can manage own warehouse" ON warehouses_warehouse;
                DROP POLICY IF EXISTS "Staff can manage all warehouses" ON warehouses_warehouse;
                ALTER TABLE warehouses_warehouse DISABLE ROW LEVEL SECURITY;
            """,
        ),
    ]
