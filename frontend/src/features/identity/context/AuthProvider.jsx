import { useCallback, useEffect, useMemo, useState } from "react";

import { clearAuthToken, getAuthToken, setAuthToken } from "../../../services/authToken";
import { identityApi } from "../api/identityApi";
import { ROLE_LABELS } from "../constants/permissions";
import { AuthContext } from "./authContext";

function normalizeAccount(account) {
  const role = typeof account.role === "string" ? account.role : account.role?.name;
  return { ...account, role, roleLabel: ROLE_LABELS[role] ?? role ?? "Không xác định" };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(getAuthToken()));

  const loadCurrentUser = useCallback(async () => {
    if (!getAuthToken()) {
      setUser(null);
      setIsLoading(false);
      return null;
    }
    setIsLoading(true);
    try {
      const account = normalizeAccount(await identityApi.getCurrentUser());
      setUser(account);
      return account;
    } catch (error) {
      if (error.status === 401 || error.status === 403) clearAuthToken();
      setUser(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();

    function handleUnauthenticated() {
      setUser(null);
      setIsLoading(false);
    }

    window.addEventListener("logistics:unauthenticated", handleUnauthenticated);
    return () => window.removeEventListener("logistics:unauthenticated", handleUnauthenticated);
  }, [loadCurrentUser]);

  const value = useMemo(() => ({
    user,
    isLoading,
    async login(credentials) {
      const token = await identityApi.login(credentials);
      setAuthToken(token.access_token);
      try {
        const account = normalizeAccount(await identityApi.getCurrentUser());
        setUser(account);
        return account;
      } catch (error) {
        clearAuthToken();
        setUser(null);
        throw error;
      }
    },
    logout() {
      clearAuthToken();
      setUser(null);
    },
    refreshUser: loadCurrentUser,
  }), [isLoading, loadCurrentUser, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
