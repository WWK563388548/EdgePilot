const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
}

export class ApiError extends Error {
  detail?: string;
  status: number;

  constructor(status: number, detail?: string) {
    super(detail ? `Request failed: ${status}: ${detail}` : `Request failed: ${status}`);
    this.detail = detail;
    this.status = status;
  }
}

export function queryString(params: Record<string, string | number | boolean | undefined>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function responseErrorDetail(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  try {
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        return payload.detail;
      }
      if (Array.isArray(payload.detail)) {
        return payload.detail
          .map((item) =>
            typeof item === "object" && item !== null && "msg" in item
              ? String((item as { msg: unknown }).msg)
              : String(item)
          )
          .join("; ");
      }
    }

    const text = await response.text();
    return text || undefined;
  } catch {
    return undefined;
  }
}

export async function getJson<T>(path: string): Promise<T> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await responseErrorDetail(response));
  }

  return response.json() as Promise<T>;
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await responseErrorDetail(response));
  }

  return response.json() as Promise<T>;
}

export async function patchJson<T>(path: string, body?: unknown): Promise<T> {
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await responseErrorDetail(response));
  }

  return response.json() as Promise<T>;
}
