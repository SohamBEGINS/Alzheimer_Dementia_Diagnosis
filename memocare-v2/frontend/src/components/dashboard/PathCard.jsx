import React from 'react'

export default function PathCard({
  topLabel,
  icon,
  iconGlowColor,
  accentColor,
  shadowColor,
  title,
  description,
  buttonLabel,
  onClick,
}) {
  const [hovered, setHovered] = React.useState(false)
  const [btnHovered, setBtnHovered] = React.useState(false)

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f5f5f0',
        borderRadius: '16px',
        padding: '48px 40px',
        cursor: 'pointer',
        transition: 'transform 0.25s ease, box-shadow 0.25s ease',
        border: `4px solid ${accentColor}`,
        boxShadow: hovered ? `14px 14px 0px ${shadowColor}` : `8px 8px 0px ${shadowColor}`,
        transform: hovered ? 'translateY(-6px)' : 'translateY(0)',
        flex: 1,
        minWidth: 0,
      }}
    >
      {/* Top label */}
      <p style={{
        fontSize: '20px',
        fontWeight: '700',
        color: '#1a1a1a',
        marginBottom: '28px',
        fontFamily: 'Space Mono, monospace',
      }}>
        {topLabel}
      </p>

      {/* Icon box */}
      <div style={{
        width: '96px',
        height: '96px',
        borderRadius: '20px',
        backgroundColor: '#0a0a0c',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '32px',
        boxShadow: `0 0 30px 4px ${iconGlowColor}`,
        flexShrink: 0,
      }}>
        {icon}
      </div>

      {/* Title */}
      <h2 style={{
        fontSize: '52px',
        fontWeight: '900',
        color: '#1a1a1a',
        lineHeight: '1.05',
        marginBottom: '20px',
        fontFamily: 'Dela Gothic One, cursive',
        letterSpacing: '-1px',
      }}>
        {title.split('\n').map((line, i) => (
          <React.Fragment key={i}>{line}{i < title.split('\n').length - 1 && <br/>}</React.Fragment>
        ))}
      </h2>

      {/* Description */}
      <p style={{
        fontSize: '20px',
        color: '#555',
        lineHeight: '1.65',
        flexGrow: 1,
        fontFamily: 'Space Mono, monospace',
        marginBottom: '40px',
      }}>
        {description}
      </p>

      {/* CTA Button */}
      <button
        onMouseEnter={() => setBtnHovered(true)}
        onMouseLeave={() => setBtnHovered(false)}
        onClick={(e) => { e.stopPropagation(); onClick && onClick(); }}
        style={{
          width: '100%',
          padding: '18px 0',
          fontSize: '20px',
          fontWeight: '700',
          borderRadius: '10px',
          backgroundColor: btnHovered ? accentColor : '#0a0a0c',
          color: btnHovered ? '#0a0a0c' : accentColor,
          border: `3px solid ${accentColor}`,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          fontFamily: 'Space Mono, monospace',
          letterSpacing: '0.5px',
        }}
      >
        {buttonLabel}
      </button>
    </div>
  )
}
