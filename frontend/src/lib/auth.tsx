"use client";

import { Auth0Provider, useAuth0 } from "@auth0/auth0-react";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo
} from "react";

import { setAccessTokenProvider } from "@/lib/api";

type AppAuthState = {
  enabled: boolean;
  ready: boolean;
  isAuthenticated: boolean;
  userLabel: string;
  login: () => Promise<void>;
  logout: () => void;
};

const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";
const auth0Domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN ?? "";
const auth0ClientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID ?? "";
const auth0Audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE ?? "";
const auth0RedirectUri =
  process.env.NEXT_PUBLIC_AUTH0_REDIRECT_URI ?? "http://localhost:3000";

const disabledAuthState: AppAuthState = {
  enabled: false,
  ready: true,
  isAuthenticated: true,
  userLabel: "Local Dev",
  login: async () => undefined,
  logout: () => undefined
};

const AuthContext = createContext<AppAuthState>(disabledAuthState);

function Auth0StateBridge({ children }: { children: ReactNode }) {
  const auth0 = useAuth0();

  useEffect(() => {
    if (!auth0.isAuthenticated) {
      setAccessTokenProvider(null);
      return;
    }
    setAccessTokenProvider(async () => auth0.getAccessTokenSilently());
    return () => setAccessTokenProvider(null);
  }, [auth0]);

  const value = useMemo<AppAuthState>(
    () => ({
      enabled: true,
      ready: !auth0.isLoading,
      isAuthenticated: auth0.isAuthenticated,
      userLabel: auth0.user?.email ?? auth0.user?.name ?? "Authenticated",
      login: () => auth0.loginWithRedirect(),
      logout: () =>
        auth0.logout({
          logoutParams: {
            returnTo: auth0RedirectUri
          }
        })
    }),
    [auth0]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AppAuthProvider({ children }: { children: ReactNode }) {
  if (!authEnabled) {
    return <AuthContext.Provider value={disabledAuthState}>{children}</AuthContext.Provider>;
  }

  if (!auth0Domain || !auth0ClientId || !auth0Audience) {
    const misconfiguredState: AppAuthState = {
      enabled: true,
      ready: true,
      isAuthenticated: false,
      userLabel: "Auth not configured",
      login: async () => undefined,
      logout: () => undefined
    };
    return <AuthContext.Provider value={misconfiguredState}>{children}</AuthContext.Provider>;
  }

  return (
    <Auth0Provider
      authorizationParams={{
        audience: auth0Audience,
        redirect_uri: auth0RedirectUri
      }}
      cacheLocation="memory"
      clientId={auth0ClientId}
      domain={auth0Domain}
    >
      <Auth0StateBridge>{children}</Auth0StateBridge>
    </Auth0Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
