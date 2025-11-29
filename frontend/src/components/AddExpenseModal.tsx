import { useState } from 'react'
import { X, Plus, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface AddExpenseModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const CATEGORIES = [
  { id: 'food', name: 'Food', icon: '🍜' },
  { id: 'fuel', name: 'Fuel', icon: '⛽' },
  { id: 'transport', name: 'Transport', icon: '🚌' },
  { id: 'phone', name: 'Phone/Data', icon: '📱' },
  { id: 'medical', name: 'Medical', icon: '💊' },
  { id: 'entertainment', name: 'Entertainment', icon: '🎬' },
  { id: 'shopping', name: 'Shopping', icon: '🛍️' },
  { id: 'family', name: 'Family', icon: '👨‍👩‍👧' },
  { id: 'repair', name: 'Repair', icon: '🔧' },
  { id: 'other', name: 'Other', icon: '📋' },
]

export default function AddExpenseModal({ isOpen, onClose, onSuccess }: AddExpenseModalProps) {
  const [category, setCategory] = useState('')
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!category || !amount) {
      toast.error('Please select category and enter amount')
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/expenses/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          category,
          amount: parseFloat(amount),
          description: description || undefined,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to add expense')
      }

      await response.json()
      toast.success(`Expense of ₹${amount} recorded`)
      
      // Reset form
      setCategory('')
      setAmount('')
      setDescription('')
      onSuccess()
      onClose()
    } catch (error) {
      toast.error('Failed to add expense')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Add Expense 💸</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <div className="grid grid-cols-5 gap-2">
              {CATEGORIES.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setCategory(c.name)}
                  className={`flex flex-col items-center p-2 rounded-lg border-2 transition-all ${
                    category === c.name
                      ? 'border-red-500 bg-red-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-xl">{c.icon}</span>
                  <span className="text-xs mt-1 text-gray-600">{c.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount (₹)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0"
                className="w-full pl-8 pr-4 py-3 text-2xl font-bold border rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
            </div>
            {/* Quick amounts */}
            <div className="flex gap-2 mt-2">
              {[50, 100, 200, 500].map((amt) => (
                <button
                  key={amt}
                  type="button"
                  onClick={() => setAmount(amt.toString())}
                  className="px-3 py-1 text-sm bg-gray-100 rounded-full hover:bg-gray-200"
                >
                  ₹{amt}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Lunch, Petrol refill"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !category || !amount}
            className="w-full py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Plus size={20} />
                Record ₹{amount || '0'} Expense
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
