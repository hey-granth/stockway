# Enable RLS on inventory table

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on inventory_item table
                ALTER TABLE inventory_item ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to inventory" ON inventory_item;
                DROP POLICY IF EXISTS "All users can view inventory" ON inventory_item;
                DROP POLICY IF EXISTS "Warehouse admins can manage own inventory" ON inventory_item;
                DROP POLICY IF EXISTS "Staff can manage all inventory" ON inventory_item;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to inventory"
                ON inventory_item
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: All authenticated users can view inventory (for ordering)
                CREATE POLICY "All users can view inventory"
                ON inventory_item
                FOR SELECT
                TO authenticated
                USING (true);
                
                -- Policy: Warehouse admins can manage inventory in their warehouse
                CREATE POLICY "Warehouse admins can manage own inventory"
                ON inventory_item
                FOR ALL
                TO authenticated
                USING (
                    warehouse_id IN (
                        SELECT id FROM warehouses_warehouse 
                        WHERE admin_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                )
                WITH CHECK (
                    warehouse_id IN (
                        SELECT id FROM warehouses_warehouse 
                        WHERE admin_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                );
                
                -- Policy: Staff can manage all inventory
                CREATE POLICY "Staff can manage all inventory"
                ON inventory_item
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
                DROP POLICY IF EXISTS "Service role has full access to inventory" ON inventory_item;
                DROP POLICY IF EXISTS "All users can view inventory" ON inventory_item;
                DROP POLICY IF EXISTS "Warehouse admins can manage own inventory" ON inventory_item;
                DROP POLICY IF EXISTS "Staff can manage all inventory" ON inventory_item;
                ALTER TABLE inventory_item DISABLE ROW LEVEL SECURITY;
            """,
        ),
    ]
