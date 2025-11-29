import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { 
  Home, 
  MessageCircle, 
  Target, 
  CreditCard, 
  Settings, 
  LogOut,
  Menu,
  X 
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '../store/authStore'

const navItems = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/chat', icon: MessageCircle, label: 'Chat' },
  { to: '/goals', icon: Target, label: 'Goals' },
  { to: '/advances', icon: CreditCard, label: 'Advances' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-primary-600">💰 GigMoney Guru</h1>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-gray-600 hover:text-gray-900"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-50
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-primary-600">💰 GigMoney Guru</h1>
          <p className="text-sm text-gray-500 mt-1">Your AI Financial Coach</p>
        </div>

        {/* User info */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <p className="text-sm font-medium text-gray-900">{user?.name || 'User'}</p>
          <p className="text-xs text-gray-500">{user?.email}</p>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setIsMobileMenuOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-lg
                transition-colors duration-200
                ${isActive 
                  ? 'bg-primary-50 text-primary-700 font-medium' 
                  : 'text-gray-600 hover:bg-gray-100'
                }
              `}
            >
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="absolute bottom-4 left-4 right-4">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-lg
              text-gray-600 hover:bg-red-50 hover:text-red-600
              transition-colors duration-200"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default Layout
