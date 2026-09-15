export function validateOrder(id: string): string {
  return `valid:${id}`;
}

export function submitOrder(id: string): string {
  return validateOrder(id);
}
