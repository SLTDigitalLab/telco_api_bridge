import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Consistent date formatting to prevent hydration mismatches
export function formatTime(date: Date): string {
  // Ensure we have a valid date
  if (!date || isNaN(date.getTime())) {
    return '12:00 AM'
  }
  
  const hours = date.getHours()
  const minutes = date.getMinutes()
  const ampm = hours >= 12 ? 'PM' : 'AM'
  const displayHours = hours % 12 || 12
  const displayMinutes = minutes.toString().padStart(2, '0')
  return `${displayHours.toString().padStart(2, '0')}:${displayMinutes} ${ampm}`
}
