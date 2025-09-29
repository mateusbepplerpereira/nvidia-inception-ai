import { NavLink, Outlet } from 'react-router-dom';
import NotificationDropdown from './NotificationDropdown';

function Layout() {
  return (
    <div className="min-h-screen bg-nvidia-dark">
      <nav className="bg-nvidia-gray border-b border-nvidia-lightGray">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="ml-10 flex items-center space-x-4">
                <div className="flex items-center flex-shrink-0">
                  <img src="/public/logo-nvidia.svg" alt="NVIDIA Logo" className="h-12 w-auto" />
                </div>

                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-nvidia-green text-nvidia-dark'
                        : 'text-gray-300 hover:bg-nvidia-lightGray hover:text-white'
                    }`
                  }
                >
                  <ion-icon name="analytics-outline" className="mr-1"></ion-icon>
                  Dashboard
                </NavLink>
                <NavLink
                  to="/startups"
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-nvidia-green text-nvidia-dark'
                        : 'text-gray-300 hover:bg-nvidia-lightGray hover:text-white'
                    }`
                  }
                >
                  <ion-icon name="business-outline" className="mr-1"></ion-icon>
                  Startups
                </NavLink>
                <NavLink
                  to="/logs"
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-nvidia-green text-nvidia-dark'
                        : 'text-gray-300 hover:bg-nvidia-lightGray hover:text-white'
                    }`
                  }
                >
                  <ion-icon name="document-text-outline" className="mr-1"></ion-icon>
                  Logs
                </NavLink>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <NotificationDropdown />
              <NavLink
                to="/settings"
                className="text-gray-300 hover:text-white"
              >
                <ion-icon name="settings-outline" size="large"></ion-icon>
              </NavLink>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;