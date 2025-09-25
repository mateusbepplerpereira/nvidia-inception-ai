import { NavLink, Outlet } from 'react-router-dom';

function Layout() {
  return (
    <div className="min-h-screen bg-nvidia-dark">
      <nav className="bg-nvidia-gray border-b border-nvidia-lightGray">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="ml-10 flex items-baseline space-x-4">
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
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-300 hover:text-white">
                <ion-icon name="notifications-outline" size="large"></ion-icon>
              </button>
              <button className="text-gray-300 hover:text-white">
                <ion-icon name="settings-outline" size="large"></ion-icon>
              </button>
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