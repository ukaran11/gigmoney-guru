import { useState, useEffect } from 'react'
import { Plus, Target, Calendar, Trash2 } from 'lucide-react'
import { goalsAPI } from '../lib/api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

interface Goal {
  id: string
  name: string
  emoji: string
  target_amount: number
  current_amount: number
  progress_percent: number
  target_date: string | null
  priority: number
  status: string
}

function Goals() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newGoal, setNewGoal] = useState({
    name: '',
    emoji: '🎯',
    target_amount: '',
    target_date: '',
    priority: 1,
  })

  useEffect(() => {
    loadGoals()
  }, [])

  const loadGoals = async () => {
    try {
      const response = await goalsAPI.list()
      setGoals(response.data.goals || [])
    } catch (error) {
      toast.error('Failed to load goals')
    } finally {
      setIsLoading(false)
    }
  }

  const createGoal = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await goalsAPI.create({
        name: newGoal.name,
        emoji: newGoal.emoji,
        target_amount: parseFloat(newGoal.target_amount),
        target_date: newGoal.target_date ? `${newGoal.target_date}T00:00:00` : undefined,
        priority: newGoal.priority,
      })
      toast.success('Goal created! 🎯')
      setShowAddModal(false)
      setNewGoal({ name: '', emoji: '🎯', target_amount: '', target_date: '', priority: 1 })
      loadGoals()
    } catch (error) {
      toast.error('Failed to create goal')
    }
  }

  const contributeToGoal = async (goalId: string, amount: number) => {
    try {
      const response = await goalsAPI.contribute(goalId, amount)
      toast.success(response.data.message)
      loadGoals()
    } catch (error) {
      toast.error('Failed to add contribution')
    }
  }

  const deleteGoal = async (goalId: string) => {
    if (!confirm('Delete this goal?')) return
    try {
      await goalsAPI.delete(goalId)
      toast.success('Goal deleted')
      loadGoals()
    } catch (error) {
      toast.error('Failed to delete goal')
    }
  }

  const emojis = ['🎯', '📚', '📱', '🏠', '🚗', '✈️', '💍', '🎓', '🪔', '🎁', '💰', '🏥']

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🎯 Savings Goals</h1>
          <p className="text-gray-600">Track your progress towards your dreams</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus size={20} />
          New Goal
        </button>
      </div>

      {/* Goals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {goals.map((goal) => (
          <div key={goal.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{goal.emoji}</span>
                <div>
                  <h3 className="font-semibold text-gray-900">{goal.name}</h3>
                  {goal.target_date && (
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      <Calendar size={14} />
                      {format(new Date(goal.target_date), 'MMM d, yyyy')}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => deleteGoal(goal.id)}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>

            {/* Progress */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-700">₹{goal.current_amount.toLocaleString()}</span>
                <span className="text-gray-500">₹{goal.target_amount.toLocaleString()}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-primary-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, goal.progress_percent)}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {goal.progress_percent.toFixed(1)}% complete
              </p>
            </div>

            {/* Quick add buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => contributeToGoal(goal.id, 100)}
                className="flex-1 py-2 text-sm bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors"
              >
                +₹100
              </button>
              <button
                onClick={() => contributeToGoal(goal.id, 500)}
                className="flex-1 py-2 text-sm bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors"
              >
                +₹500
              </button>
              <button
                onClick={() => contributeToGoal(goal.id, 1000)}
                className="flex-1 py-2 text-sm bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors"
              >
                +₹1000
              </button>
            </div>
          </div>
        ))}

        {goals.length === 0 && (
          <div className="col-span-full text-center py-12">
            <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No goals yet</h3>
            <p className="text-gray-500 mb-4">Start by creating your first savings goal!</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Create Goal
            </button>
          </div>
        )}
      </div>

      {/* Add Goal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md animate-slide-up">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Goal</h2>
            
            <form onSubmit={createGoal} className="space-y-4">
              {/* Emoji picker */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Choose an icon</label>
                <div className="flex flex-wrap gap-2">
                  {emojis.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => setNewGoal({ ...newGoal, emoji })}
                      className={`w-10 h-10 text-xl rounded-lg border-2 transition-colors ${
                        newGoal.emoji === emoji
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Goal Name</label>
                <input
                  type="text"
                  value={newGoal.name}
                  onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g., New Phone"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target Amount (₹)</label>
                <input
                  type="number"
                  value={newGoal.target_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="15000"
                  min="100"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target Date (Optional)</label>
                <input
                  type="date"
                  value={newGoal.target_date}
                  onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Goals
