const TOKEN_STORAGE_KEY = "logistics_access_token";

export function getAuthToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAuthToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAuthToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}
