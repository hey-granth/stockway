# Enable RLS on shopkeepers tables (notifications and support tickets)

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("shopkeepers", "0002_alter_notification_options_and_more"),
    ]

    operations = [
        # Enable RLS on notifications table
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on notifications table
                ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to notifications" ON notifications;
                DROP POLICY IF EXISTS "Users can view own notifications" ON notifications;
                DROP POLICY IF EXISTS "Users can update own notifications" ON notifications;
                DROP POLICY IF EXISTS "Staff can manage all notifications" ON notifications;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to notifications"
                ON notifications
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view their own notifications
                CREATE POLICY "Users can view own notifications"
                ON notifications
                FOR SELECT
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Users can update their own notifications (mark as read)
                CREATE POLICY "Users can update own notifications"
                ON notifications
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
                
                -- Policy: Staff can manage all notifications
                CREATE POLICY "Staff can manage all notifications"
                ON notifications
                FOR ALL
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE supabase_uid = auth.uid()::text 
                        AND (is_staff = true OR is_superuser = true)
                    )
                )
                WITH CHECK (true);
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS "Service role has full access to notifications" ON notifications;
                DROP POLICY IF EXISTS "Users can view own notifications" ON notifications;
                DROP POLICY IF EXISTS "Users can update own notifications" ON notifications;
                DROP POLICY IF EXISTS "Staff can manage all notifications" ON notifications;
                ALTER TABLE notifications DISABLE ROW LEVEL SECURITY;
            """,
        ),
        # Enable RLS on support_tickets table
        migrations.RunSQL(
            sql="""
                -- Enable Row Level Security on support_tickets table
                ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
                
                -- Drop existing policies if they exist
                DROP POLICY IF EXISTS "Service role has full access to tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Users can view own tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Users can create tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Users can update own tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Staff can manage all tickets" ON support_tickets;
                
                -- Policy: Service role has full access
                CREATE POLICY "Service role has full access to tickets"
                ON support_tickets
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
                
                -- Policy: Users can view their own tickets
                CREATE POLICY "Users can view own tickets"
                ON support_tickets
                FOR SELECT
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Users can create their own tickets
                CREATE POLICY "Users can create tickets"
                ON support_tickets
                FOR INSERT
                TO authenticated
                WITH CHECK (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Users can update their own open tickets
                CREATE POLICY "Users can update own tickets"
                ON support_tickets
                FOR UPDATE
                TO authenticated
                USING (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                    AND status = 'OPEN'
                )
                WITH CHECK (
                    user_id = (
                        SELECT id FROM users WHERE supabase_uid = auth.uid()::text
                    )
                );
                
                -- Policy: Staff can view and manage all tickets
                CREATE POLICY "Staff can manage all tickets"
                ON support_tickets
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
                DROP POLICY IF EXISTS "Service role has full access to tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Users can view own tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Users can create tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Users can update own tickets" ON support_tickets;
                DROP POLICY IF EXISTS "Staff can manage all tickets" ON support_tickets;
                ALTER TABLE support_tickets DISABLE ROW LEVEL SECURITY;
            """,
        ),
    ]
