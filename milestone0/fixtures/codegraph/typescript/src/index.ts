import { submitOrder } from "./orders";

export function createOrder(id: string): string {
  return submitOrder(id);
}
