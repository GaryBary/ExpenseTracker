import { useState, useEffect } from 'react'

interface Expense {
  id: string
  date: string | null
  amount_cents: number
  currency: string
  description: string | null
  vendor: string | null
  category: string | null
}

interface FYStats {
  fy: string
  total_cents: number
  by_category: Array<{category: string, total_cents: number}>
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function Dashboard() {
  const [stats, setStats] = useState<FYStats | null>(null)
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/stats/fy`).then(r => r.json()),
      fetch(`${API_BASE}/expenses`).then(r => r.json())
    ]).then(([statsData, expensesData]) => {
      setStats(statsData)
      setExpenses(expensesData)
    }).finally(() => {
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="page">
        <div className="page-title">Dashboard</div>
        <p>Loading...</p>
      </div>
    )
  }

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(cents / 100)
  }

  return (
    <div className="page">
      <h1 className="page-title">Dashboard</h1>
      
      {stats && (
        <div className="fy-summary">
          <h2 className="section-title">Financial Year {stats.fy}</h2>
          <div className="total-card">
            <div className="total-amount">{formatCurrency(stats.total_cents)}</div>
            <div className="total-label">Total Expenses</div>
          </div>
          
          {stats.by_category.length > 0 && (
            <div className="category-breakdown">
              <h3>By Category</h3>
              <div className="category-list">
                {stats.by_category.map(cat => (
                  <div key={cat.category} className="category-item">
                    <span className="category-name">{cat.category}</span>
                    <span className="category-amount">{formatCurrency(cat.total_cents)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="recent-expenses">
        <h2 className="section-title">Recent Expenses</h2>
        {expenses.length === 0 ? (
          <p className="empty-state">No expenses yet. <a href="/capture">Add your first expense!</a></p>
        ) : (
          <div className="expense-list">
            {expenses.slice(0, 10).map(expense => (
              <div key={expense.id} className="expense-item">
                <div className="expense-main">
                  <div className="expense-vendor">
                    {expense.vendor || expense.description || 'Unknown'}
                  </div>
                  <div className="expense-amount">
                    {formatCurrency(expense.amount_cents || 0)}
                  </div>
                </div>
                <div className="expense-details">
                  <span className="expense-date">{expense.date}</span>
                  {expense.category && (
                    <span className="expense-category">{expense.category}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <style jsx>{`
        .fy-summary {
          margin-bottom: 2rem;
        }
        
        .section-title {
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: #374151;
        }
        
        .total-card {
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          color: white;
          padding: 2rem;
          border-radius: 12px;
          text-align: center;
          margin-bottom: 1.5rem;
        }
        
        .total-amount {
          font-size: 2.5rem;
          font-weight: 700;
        }
        
        .total-label {
          font-size: 1rem;
          opacity: 0.9;
        }
        
        .category-breakdown {
          margin-top: 1.5rem;
        }
        
        .category-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        
        .category-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 6px;
        }
        
        .category-name {
          font-weight: 500;
        }
        
        .category-amount {
          font-weight: 600;
          color: #2563eb;
        }
        
        .empty-state {
          text-align: center;
          color: #6b7280;
          font-style: italic;
        }
        
        .expense-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        
        .expense-item {
          padding: 1rem;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          background: white;
        }
        
        .expense-main {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }
        
        .expense-vendor {
          font-weight: 500;
          color: #1f2937;
        }
        
        .expense-amount {
          font-weight: 600;
          color: #059669;
        }
        
        .expense-details {
          display: flex;
          gap: 1rem;
          font-size: 0.875rem;
          color: #6b7280;
        }
        
        .expense-category {
          background: #dbeafe;
          color: #1e40af;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
        }
      `}</style>
    </div>
  )
}

export default Dashboard
