import { api } from "./api";

export async function verifyVehicle(payload) {
  // Environment-aware POST using shared API client
  return api.post('/verify/', payload);
}

/** Example payload:
 * {
 *   plate_number: 'BA 12 PA 3456',
 *   make: 'Toyota',
 *   model: 'Corolla',
 *   owner_name: 'Ram Bahadur',
 *   region_code: 'BA',
 *   timestamp: new Date().toISOString()
 * }
 */