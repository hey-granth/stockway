/// <reference path="./deno.d.ts" />

/**
 * Supabase Edge Function for notification delivery
 *
 * This edge function can be triggered by:
 * 1. Celery tasks (from Django) for push/SMS delivery
 * 2. Database triggers on specific tables (orders, payments)
 *
 * Deploy this to Supabase Edge Functions:
 * supabase functions deploy notification-delivery
 */

// Using Supabase Edge Functions compatible imports
import "https://deno.land/x/xhr@0.3.0/mod.ts";

// Type definitions
interface NotificationPayload {
  notification_id?: number;
  user_id: number;
  user_email?: string;
  title: string;
  message: string;
  type: "order_update" | "payment" | "system";
}

interface DeliveryResults {
  push: boolean;
  sms: boolean;
  email: boolean;
}

const DJANGO_API_URL = Deno.env.get("DJANGO_API_URL") || "http://localhost:8000";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

// CORS headers
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-trigger-source",
};

Deno.serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Parse request body
    const payload = await req.json() as NotificationPayload;
    const { notification_id, user_id, user_email, title, message, type } = payload;

    console.log(`Processing notification ${notification_id} for user ${user_id}`);

    // Option 1: Trigger Celery task in Django
    // This is the preferred approach - let Django handle the processing
    if (req.headers.get("x-trigger-source") === "database") {
      const response = await fetch(`${DJANGO_API_URL}/api/notifications/trigger/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        },
        body: JSON.stringify({
          user_id,
          title,
          message,
          type,
        }),
      });

      if (!response.ok) {
        throw new Error(`Django API returned ${response.status}`);
      }

      return new Response(
        JSON.stringify({ success: true, message: "Notification task enqueued" }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
      );
    }

    // Option 2: Direct push notification delivery
    // Only for external push/SMS, not DB storage
    // TODO: Integrate with your push notification service (FCM, OneSignal, etc.)
    // TODO: Integrate with SMS service (Twilio, etc.)

    const deliveryResults: DeliveryResults = {
      push: false,
      sms: false,
      email: false,
    };

    // Example: Send push notification
    // deliveryResults.push = await sendPushNotification(user_id, title, message);

    // Example: Send SMS
    // deliveryResults.sms = await sendSMS(user_phone, message);

    // Log delivery attempt (optional - requires notification_delivery_log table)
    // Uncomment if you create this table in your database
    /*
    const { createClient } = await import("https://esm.sh/@supabase/supabase-js@2.39.0");
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    await supabase.from("notification_delivery_log").insert({
      notification_id,
      user_id,
      push_sent: deliveryResults.push,
      sms_sent: deliveryResults.sms,
      email_sent: deliveryResults.email,
      created_at: new Date().toISOString(),
    });
    */

    return new Response(
      JSON.stringify({
        success: true,
        notification_id,
        delivery: deliveryResults,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );

  } catch (error) {
    console.error("Error processing notification:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 500 }
    );
  }
});

/**
 * Database Trigger Example (PostgreSQL)
 *
 * Create a trigger that calls this edge function when specific events occur:
 *
 * -- Trigger for new orders
 * CREATE OR REPLACE FUNCTION notify_new_order()
 * RETURNS TRIGGER AS $$
 * BEGIN
 *   PERFORM net.http_post(
 *     url := 'https://your-project.supabase.co/functions/v1/notification-delivery',
 *     headers := jsonb_build_object(
 *       'Content-Type', 'application/json',
 *       'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key'),
 *       'x-trigger-source', 'database'
 *     ),
 *     body := jsonb_build_object(
 *       'user_id', NEW.user_id,
 *       'title', 'New Order Created',
 *       'message', 'Order #' || NEW.id || ' has been created',
 *       'type', 'order_update'
 *     )
 *   );
 *   RETURN NEW;
 * END;
 * $$ LANGUAGE plpgsql;
 *
 * CREATE TRIGGER trigger_notify_new_order
 * AFTER INSERT ON orders
 * FOR EACH ROW
 * EXECUTE FUNCTION notify_new_order();
 *
 * -- Trigger for payment completion
 * CREATE OR REPLACE FUNCTION notify_payment_completion()
 * RETURNS TRIGGER AS $$
 * BEGIN
 *   IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
 *     PERFORM net.http_post(
 *       url := 'https://your-project.supabase.co/functions/v1/notification-delivery',
 *       headers := jsonb_build_object(
 *         'Content-Type', 'application/json',
 *         'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key'),
 *         'x-trigger-source', 'database'
 *       ),
 *       body := jsonb_build_object(
 *         'user_id', NEW.user_id,
 *         'title', 'Payment Completed',
 *         'message', 'Payment #' || NEW.id || ' has been completed',
 *         'type', 'payment'
 *       )
 *     );
 *   END IF;
 *   RETURN NEW;
 * END;
 * $$ LANGUAGE plpgsql;
 *
 * CREATE TRIGGER trigger_notify_payment_completion
 * AFTER UPDATE ON payments
 * FOR EACH ROW
 * EXECUTE FUNCTION notify_payment_completion();
 */

/* eslint-disable */
// Supabase Edge Functions use Deno.serve instead of serve from std/http

