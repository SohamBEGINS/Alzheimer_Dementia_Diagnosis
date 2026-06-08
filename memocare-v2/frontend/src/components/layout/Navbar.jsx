import React from 'react'
import { useNavigate } from 'react-router-dom'
import logoSrc from '../../assets/memocare_logo.png'

export default function Navbar({ userName = 'John' }) {
  const navigate = useNavigate()

  // Generate initials for avatar fallback
  const initials = userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  return (
    <nav style={{
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '20px 48px',
      backgroundColor: '#0a0a0c',
      borderBottom: '1px solid rgba(255,255,255,0.08)',
    }}>
      {/* Logo + Brand */}
      <div
        onClick={() => navigate('/')}
        style={{ display: 'flex', alignItems: 'center', gap: '14px', cursor: 'pointer' }}
      >
        <img
          src={logoSrc}
          alt="MemoCare Logo"
          style={{ width: '44px', height: '44px', objectFit: 'contain' }}
        />
        <span style={{
          fontSize: '26px',
          fontWeight: '700',
          color: '#ffffff',
          letterSpacing: '-0.5px',
          fontFamily: 'Dela Gothic One, cursive',
        }}>
          MemoCare
        </span>
      </div>

      {/* User info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{
          fontSize: '18px',
          color: '#cccccc',
          fontFamily: 'Space Mono, monospace',
        }}>
          Welcome back, {userName}
        </span>

        {/* Avatar circle */}
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          backgroundColor: '#2a2a2a',
          border: '2px solid rgba(255,255,255,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: '16px',
          fontWeight: '700',
          fontFamily: 'Space Mono, monospace',
          flexShrink: 0,
        }}>
          {initials}
        </div>
      </div>
    </nav>
  )
}
