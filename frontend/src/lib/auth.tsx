"use client";

import { Auth0Provider, useAuth0 } from "@auth0/auth0-react";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

import { api, setAccessTokenProvider } from "@/lib/api";

type AppAuthState = {
  configured: boolean;
  ready: boolean;
  isAuthenticated: boolean;
  emailVerified: boolean;
  userLabel: string;
  login: () => Promise<void>;
  logout: () => void;
  resendVerificationEmail: () => Promise<void>;
  refreshSession: () => Promise<void>;
};

const auth0Domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN ?? "";
const auth0ClientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID ?? "";
const auth0Audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE ?? "";
const auth0RedirectUri =
  process.env.NEXT_PUBLIC_AUTH0_REDIRECT_URI ?? "http://localhost:3000";
const auth0Connection = process.env.NEXT_PUBLIC_AUTH0_CONNECTION ?? "";

const unavailableAuthState: AppAuthState = {
  configured: false,
  ready: true,
  isAuthenticated: false,
  emailVerified: false,
  userLabel: "Auth not configured",
  login: async () => undefined,
  logout: () => undefined,
  resendVerificationEmail: async () => undefined,
  refreshSession: async () => undefined
};

const AuthContext = createContext<AppAuthState>(unavailableAuthState);

function Auth0StateBridge({ children }: { children: ReactNode }) {
  const auth0 = useAuth0();
  const [verifiedOverride, setVerifiedOverride] = useState(false);

  useEffect(() => {
    if (!auth0.isAuthenticated) {
      setAccessTokenProvider(null);
      setVerifiedOverride(false);
      return;
    }
    setAccessTokenProvider(async () => {
      try {
        return await auth0.getAccessTokenSilently();
      } catch {
        await auth0.loginWithRedirect({
          appState: { returnTo: window.location.pathname }
        });
        return null;
      }
    });
    return () => setAccessTokenProvider(null);
  }, [auth0]);

  const value = useMemo<AppAuthState>(
    () => ({
      configured: true,
      ready: !auth0.isLoading,
      isAuthenticated: auth0.isAuthenticated,
      emailVerified: verifiedOverride || Boolean(auth0.user?.email_verified),
      userLabel: auth0.user?.email ?? auth0.user?.name ?? "Authenticated",
      login: () =>
        auth0.loginWithRedirect({
          appState: { returnTo: window.location.pathname }
        }),
      logout: () =>
        auth0.logout({
          logoutParams: {
            returnTo: auth0RedirectUri
          }
        }),
      resendVerificationEmail: async () => {
        await api.resendVerificationEmail();
      },
      refreshSession: async () => {
        try {
          await auth0.getAccessTokenSilently({
            cacheMode: "off",
            authorizationParams: {
              audience: auth0Audience,
              redirect_uri: auth0RedirectUri,
              scope: "openid profile email offline_access"
            }
          });
          const claims = await auth0.getIdTokenClaims();
          if (claims?.email_verified) {
            setVerifiedOverride(true);
            return;
          }
        } catch {
          // Fall through to an interactive login so Auth0 can issue fresh claims.
        }

        await auth0.loginWithRedirect({
          appState: { returnTo: window.location.pathname },
          authorizationParams: {
            audience: auth0Audience,
            prompt: "login",
            redirect_uri: auth0RedirectUri,
            scope: "openid profile email offline_access"
          }
        });
      }
    }),
    [auth0, verifiedOverride]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AppAuthProvider({ children }: { children: ReactNode }) {
  if (!auth0Domain || !auth0ClientId || !auth0Audience) {
    return <AuthContext.Provider value={unavailableAuthState}>{children}</AuthContext.Provider>;
  }

  return (
    <Auth0Provider
      authorizationParams={{
        audience: auth0Audience,
        connection: auth0Connection || undefined,
        redirect_uri: auth0RedirectUri,
        scope: "openid profile email offline_access"
      }}
      cacheLocation="localstorage"
      clientId={auth0ClientId}
      domain={auth0Domain}
      useRefreshTokens
    >
      <Auth0StateBridge>{children}</Auth0StateBridge>
    </Auth0Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
