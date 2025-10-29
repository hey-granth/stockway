# Enable RLS on payments table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_payment_payee'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on payments_payment table
                ALTER TABLE payments_payment ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to payments" ON payments_payment;
                DROP POLICY IF EXISTS "Users can view own payments" ON payments_payment;
                DROP POLICY IF EXISTS "Shopkeepers can create payments" ON payments_payment;
                DROP POLICY IF EXISTS "Warehouse managers can view warehouse payments" ON payments_payment;
                DROP POLICY IF EXISTS "Riders can view their payouts" ON payments_payment;
                DROP POLICY IF EXISTS "Staff can view all payments" ON payments_payment;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to payments"
                ON payments_payment
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view payments they made or received
                CREATE POLICY "Users can view own payments"
                ON payments_payment
                FOR SELECT
                TO authenticated
                USING (
                    payer_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                    OR payee_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                    OR rider_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Shopkeepers can create payments for their orders
                CREATE POLICY "Shopkeepers can create payments"
                ON payments_payment
                FOR INSERT
                TO authenticated
                WITH CHECK (
                    payer_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                    AND payment_type = 'shopkeeper_to_warehouse'
                );
                
                -- Policy: Warehouse managers can view payments for their warehouse
                CREATE POLICY "Warehouse managers can view warehouse payments"
                ON payments_payment
                FOR SELECT
                TO authenticated
                USING (
                    warehouse_id IN (
                        SELECT id FROM warehouses_warehouse 
                        WHERE admin_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                );
                
                -- Policy: Warehouse managers can create rider payouts
                CREATE POLICY "Warehouse managers can create rider payouts"
                ON payments_payment
                FOR INSERT
                TO authenticated
                WITH CHECK (
                    warehouse_id IN (
                        SELECT id FROM warehouses_warehouse 
                        WHERE admin_id = (
                            SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                        )
                    )
                    AND payment_type = 'warehouse_to_rider'
                );
                
                -- Policy: Riders can view their payouts
                CREATE POLICY "Riders can view their payouts"
                ON payments_payment
                FOR SELECT
                TO authenticated
                USING (
                    rider_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                    OR payee_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Staff can view and manage all payments
                CREATE POLICY "Staff can view all payments"
                ON payments_payment
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
                DROP POLICY IF EXISTS "Service role has full access to payments" ON payments_payment;
                DROP POLICY IF EXISTS "Users can view own payments" ON payments_payment;
                DROP POLICY IF EXISTS "Shopkeepers can create payments" ON payments_payment;
                DROP POLICY IF EXISTS "Warehouse managers can view warehouse payments" ON payments_payment;
                DROP POLICY IF EXISTS "Warehouse managers can create rider payouts" ON payments_payment;
                DROP POLICY IF EXISTS "Riders can view their payouts" ON payments_payment;
                DROP POLICY IF EXISTS "Staff can view all payments" ON payments_payment;
                ALTER TABLE payments_payment DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]

