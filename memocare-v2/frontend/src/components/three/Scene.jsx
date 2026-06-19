import { Suspense } from 'react'
import Swarm from './Swarm'

export default function Scene() {
  return (
    <>
      <ambientLight intensity={1.0} />
      <pointLight position={[10, 10, 10]} intensity={0.5} />
      <Suspense fallback={null}>
        <Swarm />
      </Suspense>
    </>
  )
}
