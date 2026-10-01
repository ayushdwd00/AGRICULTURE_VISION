const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const RENTAL_TOKEN_KEY = "agrivision.rental.accessToken";

function requestHeaders(authenticated: boolean, json: boolean): HeadersInit {
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  if (authenticated) {
    const token = sessionStorage.getItem(RENTAL_TOKEN_KEY);
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export function saveRentalToken(token: string | null): void {
  if (token) sessionStorage.setItem(RENTAL_TOKEN_KEY, token);
  else sessionStorage.removeItem(RENTAL_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      payload &&
      typeof payload === "object" &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }
  return payload as T;
}

export async function get<T>(
  path: string,
  signal?: AbortSignal,
  authenticated = false,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    signal,
    headers: requestHeaders(authenticated, false),
  });
  return parseResponse<T>(response);
}

export async function post<T>(path: string, body: unknown, authenticated = false): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: requestHeaders(authenticated, true),
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

export async function put<T>(path: string, body: unknown, authenticated = false): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: requestHeaders(authenticated, true),
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

export async function patch<T>(path: string, body: unknown, authenticated = false): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: requestHeaders(authenticated, true),
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

export async function del<T>(path: string, authenticated = false): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: requestHeaders(authenticated, false),
  });
  return parseResponse<T>(response);
}

export async function postFile<T>(
  path: string,
  file: File,
  fields: Record<string, string> = {},
  authenticated = false,
  fileField = "image",
): Promise<T> {
  const body = new FormData();
  body.append(fileField, file);
  Object.entries(fields).forEach(([key, value]) => body.append(key, value));
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: requestHeaders(authenticated, false),
    body,
  });
  return parseResponse<T>(response);
}

export function queryString(values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && String(value).trim()) params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}
