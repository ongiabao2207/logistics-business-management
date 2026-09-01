import { useState } from "react";
import { KeyRound, LogOut, ShieldCheck } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { clearAuthToken } from "../../../services/authToken";
import { useCurrentUser } from "../hooks/useCurrentUser";
import { useLogin } from "../hooks/useLogin";
import "../identity.css";

export function IdentityLoginPage() {
  usePageTitle("Identity");

  const queryClient = useQueryClient();
  const login = useLogin();
  const currentUser = useCurrentUser();
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });

  function updateCredential(field, value) {
    setCredentials((currentCredentials) => ({
      ...currentCredentials,
      [field]: value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    login.mutate({
      username: credentials.username,
      password: credentials.password,
    });
  }

  function handleLogout() {
    clearAuthToken();
    queryClient.removeQueries({ queryKey: ["identity", "current-user"] });
    queryClient.removeQueries({ queryKey: ["contracts"] });
  }

  const user = currentUser.data;

  return (
    <>
      <PageHeader
        eyebrow="Identity Service"
        title="Login"
        description="Authenticate with Identity Service to receive a JWT for Contract Service and other business APIs."
        actions={
          <button className="button secondary" type="button" disabled>
            <KeyRound size={16} />
            Session
          </button>
        }
      />

      <section className="identity-panel">
        <div className="identity-copy">
          <span className="identity-icon">
            <ShieldCheck size={30} />
          </span>
          <h2>Identity JWT</h2>
          <p>
            After login, the token is stored in the browser and automatically attached
            to API requests by the shared httpClient.
          </p>
          {user ? (
            <div className="identity-session">
              <span>Signed in</span>
              <strong>{user.username}</strong>
              <small>{user.role?.name ?? user.role}</small>
            </div>
          ) : null}
        </div>

        <form className="identity-form" onSubmit={handleSubmit}>
          <label>
            <span>Username</span>
            <input
              autoComplete="username"
              value={credentials.username}
              onChange={(event) => updateCredential("username", event.target.value)}
              placeholder="Enter username"
              required
            />
          </label>

          <label>
            <span>Password</span>
            <input
              autoComplete="current-password"
              type="password"
              value={credentials.password}
              onChange={(event) => updateCredential("password", event.target.value)}
              placeholder="Enter password"
              required
            />
          </label>

          {login.isError ? (
            <p className="identity-error">
              {login.error?.message ?? "Login failed."}
            </p>
          ) : null}
          {login.isSuccess ? <p className="identity-success">Login successful.</p> : null}

          <div className="identity-actions">
            <button className="button" type="submit" disabled={login.isPending}>
              <KeyRound size={16} />
              {login.isPending ? "Signing in" : "Login"}
            </button>
            <button className="button secondary" type="button" onClick={handleLogout}>
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
