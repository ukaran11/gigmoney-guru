import { useState } from 'react'
import { X, Plus, Loader2, Calendar } from 'lucide-react'
import toast from 'react-hot-toast'

interface AddObligationModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const OBLIGATION_TYPES = [
  { id: 'rent', name: 'Room Rent', icon: '🏠', defaultAmount: 8000 },
  { id: 'emi', name: 'Bike EMI', icon: '🏍️', defaultAmount: 3500 },
  { id: 'mobile', name: 'Mobile Bill', icon: '📱', defaultAmount: 299 },
  { id: 'electricity', name: 'Electricity', icon: '💡', defaultAmount: 500 },
  { id: 'internet', name: 'Internet', icon: '📶', defaultAmount: 599 },
  { id: 'insurance', name: 'Insurance', icon: '🛡️', defaultAmount: 1000 },
  { id: 'loan', name: 'Personal Loan', icon: '💳', defaultAmount: 5000 },
  { id: 'other', name: 'Other', icon: '📋', defaultAmount: 0 },
]

export default function AddObligationModal({ isOpen, onClose, onSuccess }: AddObligationModalProps) {
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [dueDay, setDueDay] = useState('1')
  const [category, setCategory] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  if (!isOpen) return null

  const handleTypeSelect = (type: typeof OBLIGATION_TYPES[0]) => {
    setName(type.name)
    setCategory(type.id)
    if (type.defaultAmount > 0) {
      setAmount(type.defaultAmount.toString())
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name || !amount || !dueDay) {
      toast.error('Please fill all required fields')
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/obligations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          amount: parseFloat(amount),
          due_day: parseInt(dueDay),
          category: category || 'other',
          frequency: 'monthly',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to add obligation')
      }

      toast.success(`"${name}" added - Due on ${dueDay}th of every month`)
      
      // Reset form
      setName('')
      setAmount('')
      setDueDay('1')
      setCategory('')
      onSuccess()
      onClose()
    } catch (error) {
      toast.error('Failed to add obligation')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
          <h2 className="text-lg font-semibold">Add Monthly Bill 📅</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type of Bill
            </label>
            <div className="grid grid-cols-4 gap-2">
              {OBLIGATION_TYPES.map((type) => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => handleTypeSelect(type)}
                  className={`flex flex-col items-center p-2 rounded-lg border-2 transition-all ${
                    category === type.id
                      ? 'border-orange-500 bg-orange-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-xl">{type.icon}</span>
                  <span className="text-xs mt-1 text-gray-600 text-center">{type.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bill Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Room Rent"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            />
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
                className="w-full pl-8 pr-4 py-3 text-2xl font-bold border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
          </div>

          {/* Due Day */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar size={16} className="inline mr-1" />
              Due Date (Day of Month)
            </label>
            <select
              value={dueDay}
              onChange={(e) => setDueDay(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            >
              {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                <option key={day} value={day}>
                  {day}{day === 1 ? 'st' : day === 2 ? 'nd' : day === 3 ? 'rd' : 'th'} of every month
                </option>
              ))}
            </select>
          </div>

          {/* AI Info */}
          <div className="bg-orange-50 p-3 rounded-lg">
            <p className="text-sm text-orange-700">
              🤖 <strong>AI will:</strong> Track this bill, warn you before due dates, and auto-allocate earnings to cover it.
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !name || !amount}
            className="w-full py-3 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Plus size={20} />
                Add Bill
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
