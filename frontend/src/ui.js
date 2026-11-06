// Small display helpers shared by the admin pages.

// Bootstrap badge colour for each trek status
export function trekStatusBadge(status) {
  const colours = {
    Pending: 'bg-warning text-dark',
    Approved: 'bg-info text-dark',
    Open: 'bg-success',
    Closed: 'bg-dark',
    Ongoing: 'bg-primary',
    Completed: 'bg-secondary',
  }
  return colours[status] || 'bg-secondary'
}

// Bootstrap badge colour for each booking status
export function bookingStatusBadge(status) {
  const colours = { Booked: 'bg-success', Cancelled: 'bg-danger', Completed: 'bg-secondary' }
  return colours[status] || 'bg-secondary'
}

// '2026-12-05T10:30:00' -> '2026-12-05' (null-safe)
export function shortDate(text) {
  return text ? text.slice(0, 10) : '-'
}

// Bootstrap badge colour for each difficulty
export function difficultyBadge(difficulty) {
  const colours = { Easy: 'bg-success', Moderate: 'bg-warning text-dark', Hard: 'bg-danger' }
  return colours[difficulty] || 'bg-secondary'
}
