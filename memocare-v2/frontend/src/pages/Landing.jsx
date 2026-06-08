import React from 'react'
import { Canvas } from '@react-three/fiber'
import Scene from '../components/three/Scene'
import AuthForm from '../components/AuthForm'

export default function Landing() {
  return (
    <div className="flex flex-col lg:flex-row w-full min-h-screen bg-[#0a0a0c] overflow-hidden">
      
      {/* LEFT PANE - Hero & 3D Brain */}
      <div className="relative w-full lg:w-[55%] h-[50vh] lg:h-screen flex flex-col items-center justify-center border-r border-white/10 bg-black">
        
        {/* Background 3D Particle Brain */}
        <div className="absolute inset-0 z-0">
          <Canvas
            camera={{ position: [0, 0, 9], fov: 75 }}
            gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
            dpr={[1, 2]}
          >
            <Scene />
          </Canvas>
        </div>

        {/* Dark overlay behind text */}
        <div className="absolute inset-0 z-[1] bg-black/40 pointer-events-none"></div>
        
        {/* Foreground Text Layer */}
        <div className="relative z-10 flex flex-col items-center justify-center pointer-events-none px-6 w-full mb-48">
          
          <h1 className="text-6xl font-extrabold tracking-tighter text-white drop-shadow-[0_0_15px_rgba(0,0,0,0.8)]">
            MemoCare
          </h1>
          
          <div className="mt-3 bg-black/40 backdrop-blur-md px-5 py-2.5 rounded-xl border border-white/5">
            <p className="text-slate-200 text-sm md:text-base font-medium tracking-wide text-center drop-shadow-md">
              Advanced Alzheimer's detection and classification
              <br/>
              <span className="text-slate-400 text-xs mt-1 block font-normal">powered by deep learning.</span>
            </p>
          </div>
        </div>
      </div>

      {/* RIGHT PANE - Auth Form */}
      <div className="w-full lg:w-[45%] h-[50vh] lg:h-screen flex items-center justify-center p-8 lg:p-16 bg-zinc-950">
        <AuthForm />
      </div>

    </div>
  )
}
