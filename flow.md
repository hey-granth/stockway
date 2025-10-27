### *1. Customer (Shopkeeper)*

* [ ] OTP Based Authentication (request/verify)
* [ ] Profile completion (shop name, address, GST number, location via PostGIS)
* [ ] Multi-shop management (add/manage multiple shops per user)
* [ ] Discover nearby warehouses (PostGIS distance-based queries)
* [ ] Product browsing with filters (category, availability, price)
* [ ] Cart system (add/remove items, quantity management)
* [ ] Order placement (create, update, cancel)
* [ ] Order tracking (status, assigned rider, estimated delivery time)
* [ ] Payment integration (UPI/QR tracking or transaction history)
* [ ] Notifications (order status, warehouse updates, promotions)
* [ ] Feedback system (submit issues or reviews)
* [ ] Analytics (monthly orders, spend trends, delivery history)

---

### *2. Warehouse*

* [ ] Profile setup (name, address, GPS, contact info)
* [ ] Inventory management (CRUD for items, stock updates, price changes)
* [ ] Order dashboard (incoming, pending, delivered)
* [ ] Assign riders to orders (manual or auto-assignment)
* [ ] Delivery charge calculation (based on distance, configurable rate/km)
* [ ] Payment tracking for orders and rider payouts
* [ ] Notifications (incoming orders, low-stock alerts)
* [ ] Warehouse-level analytics (orders/day, delivery success rate, revenue)

---

### *3. Rider*

* [ ] Profile registration (linked to warehouse, contact info)
* [ ] Availability toggle (active/inactive for delivery)
* [ ] Assigned delivery list (fetch orders assigned to them)
* [ ] Delivery status update (accepted, in-transit, delivered)
* [ ] Distance tracking (calculate actual vs expected delivery distance)
* [ ] Payout computation (auto or manual approval by warehouse)
* [ ] Delivery history and performance metrics (orders completed, total distance, earnings)

---

### *4. Admin*

* [ ] Admin dashboard for user management (warehouses, riders, customers)
* [ ] Approve/reject warehouse registrations
* [ ] Oversee and modify inventory if needed
* [ ] Monitor system-wide analytics (orders, revenue, region-wise performance)
* [ ] Manage payouts and disputes (rider or warehouse-related)
* [ ] Role management and access control
* [ ] Push notifications or alerts across all users

---

### *5. Core & Infrastructure*

* [ ] Global error handling and custom exception middleware
* [ ] Logging and request tracking (via DRF or Django signals)
* [ ] API rate limiting and throttling (DRF)
* [ ] Background tasks for notifications or payout computations (Celery + Redis)
* [ ] Environment setup for staging/production (Supabase + PostGIS + DRF config)
* [ ] Comprehensive API documentation (Swagger/OpenAPI or drf-spectacular)
* [ ] Unit and integration tests for major flows
* [ ] CI/CD pipeline setup (GitHub Actions)
* [ ] Containerization (Docker + Docker Compose for local dev)