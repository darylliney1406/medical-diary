export function getBPCategory(s, d) {
  if (!s || !d) return { label: '--', classes: 'bg-gray-100 text-gray-600', color: 'text-gray-400' }
  if (s >= 180 || d >= 120) return { label: 'Stage 3 – Severe', classes: 'bg-purple-100 text-purple-900', color: 'text-purple-600' }
  if (s >= 160 || d >= 100) return { label: 'Stage 2 Hypertension', classes: 'bg-red-100 text-red-800', color: 'text-red-600' }
  if (s >= 140 || d >= 90)  return { label: 'Stage 1 Hypertension', classes: 'bg-orange-100 text-orange-800', color: 'text-orange-600' }
  if (s >= 120 || d >= 80)  return { label: 'Pre-hypertension', classes: 'bg-yellow-100 text-yellow-800', color: 'text-yellow-600' }
  if (s < 90  && d < 60)    return { label: 'Low', classes: 'bg-blue-100 text-blue-800', color: 'text-blue-600' }
  return { label: 'Normal', classes: 'bg-green-100 text-green-800', color: 'text-green-600' }
}
export function useBPCategory() { return { getBPCategory } }
