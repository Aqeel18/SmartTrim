import React, { useEffect, useState } from 'react'
import { fetchValidations } from '../api'

export default function Gallery() {
  const [data, setData] = useState({ matting: [], pipeline: [] })
  const [error, setError] = useState('')
  const [modal, setModal] = useState(null)

  useEffect(() => {
    fetchValidations()
      .then(setData)
      .catch((e) => setError(e.message || 'Failed to load validations'))
  }, [])

  const Card = ({ src, title, onClick }) => (
    <button onClick={onClick} className="group relative overflow-hidden rounded-xl bg-white/5 border border-white/10 shadow hover:shadow-cyan-500/10 transition">
      {/* eslint-disable-next-line jsx-a11y/alt-text */}
      <img src={src} className="w-full h-40 object-cover" />
      <div className="absolute bottom-0 inset-x-0 p-2 bg-gradient-to-t from-black/60 to-transparent text-left text-xs text-white opacity-90">{title}</div>
    </button>
  )

  return (
    <div className="space-y-10">
      <h2 className="text-2xl font-bold">Validation Gallery</h2>
      {error && <div className="text-red-400 text-sm">{error}</div>}

      <section>
        <h3 className="font-semibold mb-3">Matting validation</h3>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {data.matting?.map((x, i) => (
            <Card key={i} src={x} title={`Matting ${i + 1}`} onClick={() => setModal({ src: x })} />
          ))}
        </div>
      </section>

      <section>
        <h3 className="font-semibold mb-3">Full pipeline validation</h3>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {data.pipeline?.map((x, i) => (
            <Card key={i} src={x} title={`Pipeline ${i + 1}`} onClick={() => setModal({ src: x })} />
          ))}
        </div>
      </section>

      {modal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-6" onClick={() => setModal(null)}>
          {/* eslint-disable-next-line jsx-a11y/alt-text */}
          <img src={modal.src} className="max-h-[85vh] rounded-xl shadow-2xl" />
        </div>
      )}
    </div>
  )
}

