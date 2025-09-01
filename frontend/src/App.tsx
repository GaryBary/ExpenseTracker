import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Capture from './pages/Capture'
import './App.css'

function App() {
  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-content">
          <h1 className="nav-title">Expense Tracker</h1>
          <div className="nav-links">
            <Link to="/" className="nav-link">Dashboard</Link>
            <Link to="/capture" className="nav-link">Add Expense</Link>
          </div>
        </div>
      </nav>
      
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/capture" element={<Capture />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
