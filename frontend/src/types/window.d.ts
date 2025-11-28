export {};

declare global {
  interface Window {
    ethereum?: {
      isMetaMask?: boolean;
      request: (request: { method: string; params?: unknown[] }) => Promise<unknown>;
      on: (eventName: string, callback: (params: unknown) => void) => void;
      removeListener: (eventName: string, callback: (params: unknown) => void) => void;
    };
  }
}
