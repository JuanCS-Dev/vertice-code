import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility to merge Tailwind classes conditionally.
 * Solves conflicts like "bg-red-500 bg-blue-500" -> "bg-blue-500".
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
