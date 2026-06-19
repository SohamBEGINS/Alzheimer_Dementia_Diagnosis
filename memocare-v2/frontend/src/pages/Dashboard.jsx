import React from 'react'
import Navbar from '../components/layout/Navbar'
import PathCard from '../components/dashboard/PathCard'
import { Particles } from '../components/ui/particles'

const BrainIcon = () => (
  <svg viewBox="0 0 64 64" width="52" height="52" fill="none" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M32 8C20 8 12 16 12 27c0 5 2 9.5 5 13 .5 3.5 1 7 1 10h28c0-3 .5-6.5 1-10 3-3.5 5-8 5-13 0-11-8-19-20-19z"/>
    <path d="M32 8v44M22 20c0 0 4 3 10 3s10-3 10-3M18 30c0 0 5 4 14 4s14-4 14-4"/>
  </svg>
)

const ChecklistIcon = () => (
  <svg viewBox="0 0 64 64" width="52" height="52" fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="12" y="8" width="40" height="48" rx="6"/>
    <path d="M22 24h20"/>
    <path d="M22 32h20"/>
    <path d="M22 40h14"/>
    <path d="M16 24l2 2 4-4"/>
    <path d="M16 32l2 2 4-4"/>
    <path d="M16 40l2 2 4-4"/>
  </svg>
)

export default function Dashboard() {
  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      backgroundColor: '#0a0a0c',
      overflow: 'hidden',
    }}>
      
      {/* Interactive Particle Background */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0 }}>
        <Particles
          quantity={200}
          ease={80}
          color="#ffffff"
          refresh
        />
      </div>

      {/* Foreground Content */}
      <div style={{
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
      }}>
        <Navbar userName="John" />

        {/* Main content */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 48px',
      }}>

        {/* Cards row */}
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '48px',
          width: '100%',
          maxWidth: '1100px',
          alignItems: 'stretch',
        }}>
          <PathCard
            topLabel="MRI Brain Scan"
            icon={<BrainIcon />}
            iconGlowColor="rgba(6, 182, 212, 0.25)"
            accentColor="#06b6d4"
            shadowColor="rgba(6, 182, 212, 0.45)"
            title={"Analyze\nMRI Scan"}
            description="Upload a brain MRI for AI-powered dementia detection and classification."
            buttonLabel="Learn More"
            onClick={() => {}}
          />

          <PathCard
            topLabel="Cognitive Assessment"
            icon={<ChecklistIcon />}
            iconGlowColor="rgba(245, 158, 11, 0.25)"
            accentColor="#f59e0b"
            shadowColor="rgba(245, 158, 11, 0.45)"
            title={"Take\nAssessment"}
            description="Answer a series of questions to evaluate cognitive health and detect early signs."
            buttonLabel="Learn More"
            onClick={() => {}}
          />
        </div>

        {/* Disclaimer */}
        <p style={{
          marginTop: '40px',
          fontSize: '14px',
          color: '#888',
          textAlign: 'center',
          maxWidth: '600px',
          fontFamily: 'Space Mono, monospace',
          lineHeight: '1.7',
          backgroundColor: 'rgba(10, 10, 12, 0.7)',
          padding: '12px 24px',
          borderRadius: '8px',
          backdropFilter: 'blur(4px)',
        }}>
          ⚠️ MemoCare is an assistive tool and does not replace professional medical diagnosis. Always consult a licensed physician.
        </p>
      </div>
    </div>
    </div>
  )
}
