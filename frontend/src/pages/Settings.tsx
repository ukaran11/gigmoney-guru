import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { useDashboardStore } from '../store/dashboardStore'
import { User, Globe, Trash2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

function Settings() {
  const { user, updateProfile, logout } = useAuthStore()
  const { resetData, seedDemoData } = useDashboardStore()
  const [name, setName] = useState(user?.name || '')
  const [language, setLanguage] = useState(user?.preferred_language || 'english')
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await updateProfile({ name, preferred_language: language })
      toast.success('Settings saved!')
    } catch {
      toast.error('Failed to save settings')
    } finally {
      setIsSaving(false)
    }
  }

  const handleResetData = async () => {
    if (!confirm('This will delete ALL your financial data. Are you sure?')) return
    try {
      await resetData()
      toast.success('All data cleared')
    } catch {
      toast.error('Failed to reset data')
    }
  }

  const handleReloadDemo = async () => {
    if (!confirm('This will replace your current data with demo data. Continue?')) return
    try {
      await seedDemoData()
      toast.success('Demo data loaded!')
    } catch {
      toast.error('Failed to load demo data')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">⚙️ Settings</h1>
        <p className="text-gray-600">Manage your account preferences</p>
      </div>

      {/* Profile Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <User size={20} />
          Profile
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-500 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Your name"
            />
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Language Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Globe size={20} />
          Language Preference
        </h2>
        
        <div className="space-y-3">
          {[
            { value: 'english', label: 'English', emoji: '🇬🇧' },
            { value: 'hinglish', label: 'Hinglish (Hindi + English)', emoji: '🇮🇳' },
            { value: 'hindi', label: 'Hindi', emoji: '🇮🇳' },
          ].map((lang) => (
            <label
              key={lang.value}
              className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                language === lang.value
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name="language"
                value={lang.value}
                checked={language === lang.value}
                onChange={(e) => setLanguage(e.target.value)}
                className="sr-only"
              />
              <span className="text-2xl">{lang.emoji}</span>
              <span className="font-medium text-gray-900">{lang.label}</span>
              {language === lang.value && (
                <span className="ml-auto text-primary-600">✓</span>
              )}
            </label>
          ))}
        </div>

        <button
          onClick={handleSave}
          disabled={isSaving}
          className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
        >
          {isSaving ? 'Saving...' : 'Save Language'}
        </button>
      </div>

      {/* Demo & Data Controls */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🎮 Demo Controls</h2>
        <p className="text-sm text-gray-600 mb-4">
          For testing and demonstration purposes
        </p>
        
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleReloadDemo}
            className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
          >
            <RefreshCw size={18} />
            Load Ravi's Demo Data
          </button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-red-50 rounded-xl p-6 border border-red-200">
        <h2 className="text-lg font-semibold text-red-800 mb-4">⚠️ Danger Zone</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-red-700">Clear All Data</h3>
            <p className="text-sm text-red-600 mb-2">
              This will permanently delete all your financial data.
            </p>
            <button
              onClick={handleResetData}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <Trash2 size={18} />
              Clear All Data
            </button>
          </div>

          <div className="pt-4 border-t border-red-200">
            <h3 className="font-medium text-red-700">Logout</h3>
            <p className="text-sm text-red-600 mb-2">
              Sign out of your account.
            </p>
            <button
              onClick={logout}
              className="px-4 py-2 border border-red-600 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
