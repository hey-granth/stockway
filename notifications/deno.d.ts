// Deno type declarations for Supabase Edge Functions
// This file provides TypeScript types for the Deno runtime

declare global {
  /**
   * Deno namespace for Deno runtime APIs
   */
  namespace Deno {
    /**
     * Environment variable access
     */
    export const env: {
      /**
       * Get an environment variable value
       * @param key - The environment variable name
       * @returns The value or undefined if not set
       */
      get(key: string): string | undefined;

      /**
       * Set an environment variable
       * @param key - The environment variable name
       * @param value - The value to set
       */
      set(key: string, value: string): void;

      /**
       * Delete an environment variable
       * @param key - The environment variable name
       */
      delete(key: string): void;

      /**
       * Convert environment to object
       */
      toObject(): Record<string, string>;
    };

    /**
     * Serve HTTP requests
     * @param handler - Request handler function
     * @param options - Server options
     */
    export function serve(
      handler: (request: Request) => Response | Promise<Response>,
      options?: {
        port?: number;
        hostname?: string;
        signal?: AbortSignal;
        onListen?: (params: { hostname: string; port: number }) => void;
        onError?: (error: unknown) => Response | Promise<Response>;
      }
    ): void;
  }

  /**
   * Request interface (Web API)
   */
  interface Request {
    readonly method: string;
    readonly url: string;
    readonly headers: Headers;
    readonly body: ReadableStream<Uint8Array> | null;
    readonly bodyUsed: boolean;
    json(): Promise<any>;
    text(): Promise<string>;
    arrayBuffer(): Promise<ArrayBuffer>;
    formData(): Promise<FormData>;
    blob(): Promise<Blob>;
    clone(): Request;
  }

  /**
   * Response interface (Web API)
   */
  interface Response {
    readonly status: number;
    readonly statusText: string;
    readonly ok: boolean;
    readonly headers: Headers;
    readonly body: ReadableStream<Uint8Array> | null;
    readonly bodyUsed: boolean;
    json(): Promise<any>;
    text(): Promise<string>;
    arrayBuffer(): Promise<ArrayBuffer>;
    formData(): Promise<FormData>;
    blob(): Promise<Blob>;
    clone(): Response;
  }

  /**
   * Response constructor
   */
  const Response: {
    new(body?: BodyInit | null, init?: ResponseInit): Response;
    error(): Response;
    redirect(url: string | URL, status?: number): Response;
  };

  /**
   * Headers interface (Web API)
   */
  interface Headers {
    append(name: string, value: string): void;
    delete(name: string): void;
    get(name: string): string | null;
    has(name: string): boolean;
    set(name: string, value: string): void;
    forEach(callbackfn: (value: string, key: string, parent: Headers) => void, thisArg?: any): void;
    entries(): IterableIterator<[string, string]>;
    keys(): IterableIterator<string>;
    values(): IterableIterator<string>;
  }

  /**
   * Fetch function (Web API)
   */
  function fetch(
    input: Request | string | URL,
    init?: RequestInit
  ): Promise<Response>;
}

export {};

