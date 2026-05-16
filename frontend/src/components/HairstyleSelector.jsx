import React from 'react'
import styles from '../styles/Selector.module.css'

export default function HairstyleSelector({ stylesList, value, onChange, recommendedSet = new Set(), reasonMap = {}, faceShape = '' }) {
  // stylesList can be a flat array or an object { category: [styles] }
  const isGrouped = !Array.isArray(stylesList)

  return (
    <div className={styles.selectorWrap}>
      <label className={styles.label}>Select Hairstyle</label>
      <select className={styles.select} value={value} onChange={(e) => onChange(e.target.value)}>
        {isGrouped ? (
          Object.entries(stylesList).map(([category, styles]) => (
            <optgroup key={category} label={category}>
              {styles.map((s) => {
                const isRec = recommendedSet.has(s.value)
                const badge = isRec ? '⭐ ' : ''
                const title = isRec ? (reasonMap[s.value] || (faceShape ? `Recommended for ${faceShape} face` : 'Recommended')) : s.label
                return (
                  <option key={s.value} value={s.value} title={title}>
                    {badge}{s.label}
                  </option>
                )
              })}
            </optgroup>
          ))
        ) : (
          stylesList.map((s) => {
            const isRec = recommendedSet.has(s.value)
            const badge = isRec ? '⭐ ' : ''
            const title = isRec ? (reasonMap[s.value] || (faceShape ? `Recommended for ${faceShape} face` : 'Recommended')) : s.label
            return (
              <option key={s.value} value={s.value} title={title}>
                {badge}{s.label}
              </option>
            )
          })
        )}
      </select>
    </div>
  )
}
