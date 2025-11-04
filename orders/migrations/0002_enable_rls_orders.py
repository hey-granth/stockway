# Enable RLS on orders tables

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        # Enable RLS on orders_order table
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on orders_order table
                ALTER TABLE orders_order ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to orders" ON orders_order;
                DROP POLICY IF EXISTS "Shopkeepers can view own orders" ON orders_order;
                DROP POLICY IF EXISTS "Shopkeepers can create orders" ON orders_order;
                DROP POLICY IF EXISTS "Staff can view all orders" ON orders_order;
                DROP POLICY IF EXISTS "Warehouse managers can manage warehouse orders" ON orders_order;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to orders"
                ON orders_order
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Shopkeepers can view and create their own orders
                CREATE POLICY "Shopkeepers can view own orders"
                ON orders_order
                FOR SELECT
                TO authenticated
                USING (
                    shopkeeper_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                CREATE POLICY "Shopkeepers can create orders"
                ON orders_order
                FOR INSERT
                TO authenticated
                WITH CHECK (
                    shopkeeper_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Warehouse managers can view and manage orders for their warehouse
                CREATE POLICY "Warehouse managers can manage warehouse orders"
                ON orders_order
                FOR ALL
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
                        AND role IN ('ADMIN', 'WAREHOUSE_MANAGER')
                    )
                )
                WITH CHECK (
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
                        AND is_staff = true
                    )
                );
                
                -- Policy: Admins can view all orders
                CREATE POLICY "Staff can view all orders"
                ON orders_order
                FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true)
                    )
                );
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS "Service role has full access to orders" ON orders_order;
                DROP POLICY IF EXISTS "Shopkeepers can view own orders" ON orders_order;
                DROP POLICY IF EXISTS "Shopkeepers can create orders" ON orders_order;
                DROP POLICY IF EXISTS "Staff can view all orders" ON orders_order;
                DROP POLICY IF EXISTS "Warehouse managers can manage warehouse orders" ON orders_order;
                ALTER TABLE orders_order DISABLE ROW LEVEL SECURITY;
            """,
        ),
        # Enable RLS on orders_orderitem table
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on orders_orderitem table
                ALTER TABLE orders_orderitem ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to order items" ON orders_orderitem;
                DROP POLICY IF EXISTS "Users can view items from accessible orders" ON orders_orderitem;
                DROP POLICY IF EXISTS "Users can manage items in accessible orders" ON orders_orderitem;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to order items"
                ON orders_orderitem
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view order items if they can view the order
                CREATE POLICY "Users can view items from accessible orders"
                ON orders_orderitem
                FOR SELECT
                TO authenticated
                USING (
                    order_id IN (
                        SELECT id FROM orders_order 
                        WHERE shopkeeper_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                        OR warehouse_id IN (
                            SELECT id FROM warehouses_warehouse 
                            WHERE admin_id = (
                                SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                            )
                        )
                    )
                    OR
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true OR role IN ('WAREHOUSE_MANAGER', 'RIDER'))
                    )
                );
                
                -- Policy: Users can manage order items if they own the order
                CREATE POLICY "Users can manage items in accessible orders"
                ON orders_orderitem
                FOR ALL
                TO authenticated
                USING (
                    order_id IN (
                        SELECT id FROM orders_order 
                        WHERE shopkeeper_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                    OR
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND is_staff = true
                    )
                )
                WITH CHECK (
                    order_id IN (
                        SELECT id FROM orders_order 
                        WHERE shopkeeper_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                    OR
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND is_staff = true
                    )
                );
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS "Service role has full access to order items" ON orders_orderitem;
                DROP POLICY IF EXISTS "Users can view items from accessible orders" ON orders_orderitem;
                DROP POLICY IF EXISTS "Users can manage items in accessible orders" ON orders_orderitem;
                ALTER TABLE orders_orderitem DISABLE ROW LEVEL SECURITY;
            """,
        ),
    ]
