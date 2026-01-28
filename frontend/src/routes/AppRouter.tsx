import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import PrivateRoute from './PrivateRoute';
import RoleBasedRoute from './RoleBasedRoute';

// Landing & Auth Pages
import LandingPage from '@/pages/common/LandingPage';
import LoginPage from '@/pages/auth/LoginPage';
import SignUpPage from '@/pages/auth/SignUpPage';

// Shopkeeper Pages
import ShopkeeperLayout from '@/pages/shopkeeper/ShopkeeperLayout';
import ShopkeeperDashboard from '@/pages/shopkeeper/ShopkeeperDashboard';
import ShopkeeperProfile from '@/pages/shopkeeper/ShopkeeperProfile';
import BrowseInventory from '@/pages/shopkeeper/BrowseInventory';
import CreateOrder from '@/pages/shopkeeper/CreateOrder';
import OrdersList from '@/pages/shopkeeper/OrdersList';
import OrderDetails from '@/pages/shopkeeper/OrderDetails';
import NearbyWarehouses from '@/pages/shopkeeper/NearbyWarehouses';

// Warehouse Pages
import WarehouseLayout from '@/pages/warehouse/WarehouseLayout';
import WarehouseDashboard from '@/pages/warehouse/WarehouseDashboard';
import WarehouseProfile from '@/pages/warehouse/WarehouseProfile';
import WarehouseInventory from '@/pages/warehouse/WarehouseInventory';
import WarehouseOrders from '@/pages/warehouse/WarehouseOrders';
import WarehouseOrderDetails from '@/pages/warehouse/WarehouseOrderDetails';
import RiderManagement from '@/pages/warehouse/RiderManagement';

// Rider Pages
import RiderLayout from '@/pages/rider/RiderLayout';
import RiderDashboard from '@/pages/rider/RiderDashboard';
import RiderProfile from '@/pages/rider/RiderProfile';
import RiderDeliveries from '@/pages/rider/RiderDeliveries';
import RiderDeliveryDetails from '@/pages/rider/RiderDeliveryDetails';
import RiderEarnings from '@/pages/rider/RiderEarnings';

// Admin Pages
import AdminLayout from '@/pages/admin/AdminLayout';
import AdminDashboard from '@/pages/admin/AdminDashboard';
import UserManagement from '@/pages/admin/UserManagement';
import WarehouseManagement from '@/pages/admin/WarehouseManagement';

// Common Pages
import NotFoundPage from '@/pages/common/NotFoundPage';
import UnauthorizedPage from '@/pages/common/UnauthorizedPage';
import DocsPage from '@/pages/common/DocsPage';
import ContactPage from '@/pages/common/ContactPage';

// Dashboard redirect component
function DashboardRedirect() {
  const { user } = useAuthStore();

  switch (user?.role) {
    case 'SHOPKEEPER':
      return <Navigate to="/shopkeeper/dashboard" replace />;
    case 'WAREHOUSE_MANAGER':
      return <Navigate to="/warehouse/dashboard" replace />;
    case 'RIDER':
      return <Navigate to="/rider/dashboard" replace />;
    case 'SUPER_ADMIN':
      return <Navigate to="/admin/dashboard" replace />;
    default:
      return <Navigate to="/" replace />;
  }
}

export default function AppRouter() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Routes>
      {/* Landing page - public route */}
      <Route
        path="/"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />}
      />

      {/* Dashboard redirect based on role */}
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardRedirect />
          </PrivateRoute>
        }
      />

      {/* Public documentation route */}
      <Route path="/docs" element={<DocsPage />} />
      <Route path="/contact" element={<ContactPage />} />

      {/* Auth routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

      {/* Shopkeeper routes */}
      <Route
        path="/shopkeeper"
        element={
          <PrivateRoute>
            <RoleBasedRoute allowedRoles={['SHOPKEEPER']}>
              <ShopkeeperLayout />
            </RoleBasedRoute>
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<ShopkeeperDashboard />} />
        <Route path="profile" element={<ShopkeeperProfile />} />
        <Route path="warehouses" element={<NearbyWarehouses />} />
        <Route path="inventory" element={<BrowseInventory />} />
        <Route path="orders" element={<OrdersList />} />
        <Route path="orders/create" element={<CreateOrder />} />
        <Route path="orders/:orderId" element={<OrderDetails />} />
      </Route>

      {/* Warehouse routes */}
      <Route
        path="/warehouse"
        element={
          <PrivateRoute>
            <RoleBasedRoute allowedRoles={['WAREHOUSE_MANAGER']}>
              <WarehouseLayout />
            </RoleBasedRoute>
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<WarehouseDashboard />} />
        <Route path="profile" element={<WarehouseProfile />} />
        <Route path="inventory" element={<WarehouseInventory />} />
        <Route path="orders" element={<WarehouseOrders />} />
        <Route path="orders/:orderId" element={<WarehouseOrderDetails />} />
        <Route path="riders" element={<RiderManagement />} />
      </Route>

      {/* Rider routes */}
      <Route
        path="/rider"
        element={
          <PrivateRoute>
            <RoleBasedRoute allowedRoles={['RIDER']}>
              <RiderLayout />
            </RoleBasedRoute>
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<RiderDashboard />} />
        <Route path="profile" element={<RiderProfile />} />
        <Route path="deliveries" element={<RiderDeliveries />} />
        <Route path="deliveries/:orderId" element={<RiderDeliveryDetails />} />
        <Route path="earnings" element={<RiderEarnings />} />
      </Route>

      {/* Admin routes */}
      <Route
        path="/admin"
        element={
          <PrivateRoute>
            <RoleBasedRoute allowedRoles={['SUPER_ADMIN']}>
              <AdminLayout />
            </RoleBasedRoute>
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="warehouses" element={<WarehouseManagement />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
