# Auth0 Setup

EdgePilot requires authentication in every environment. There is no local or staging auth bypass.

## Required Auth0 Applications

Create two Auth0 applications:

1. Single Page Application for the Next.js frontend.
2. Machine to Machine application for the backend to call the Auth0 Management API.

Create one Auth0 API:

- Identifier: use the same value as `AUTH_AUDIENCE` and `NEXT_PUBLIC_AUTH0_AUDIENCE`.
- Signing algorithm: `RS256`.
- Maximum Access Token Lifetime: `1800` seconds.
- Allow Offline Access: enabled.

## Refresh Tokens

For the Single Page Application:

- Enable Refresh Token Rotation.
- Set refresh token expiration type to expiring.
- Set absolute refresh token lifetime to `86400` seconds.
- Enable the Refresh Token grant type.

The frontend requests `offline_access`, uses Auth0 refresh token rotation, and stores the rotating token cache in browser local storage so a user can keep working across reloads within the 24-hour refresh-token lifetime. When Auth0 can no longer refresh silently, the frontend sends the user back to login.

## Email OTP Login

Enable Auth0 Passwordless with Universal Login:

1. Create or enable the Email passwordless connection.
2. Configure it to send a one-time password code.
3. Enable it for the EdgePilot SPA application.
4. Set `NEXT_PUBLIC_AUTH0_CONNECTION=email`.

This makes the EdgePilot sign-in button open the Auth0-hosted email-code login flow.

## Email Verification

EdgePilot requires `email_verified=true` before business data is accessible.

If a user signs in but the email is not verified:

- the frontend blocks the workspace;
- the backend returns `403 Email verification required` for business/dashboard endpoints;
- the frontend can call `POST /api/auth/resend-verification`;
- the backend asks Auth0 Management API to send a verification email.

The Machine to Machine application must be authorized for the Auth0 Management API with permission to send verification emails. Configure:

```text
AUTH0_MANAGEMENT_CLIENT_ID=<m2m-client-id>
AUTH0_MANAGEMENT_CLIENT_SECRET=<m2m-client-secret>
AUTH0_MANAGEMENT_AUDIENCE=https://<auth0-domain>/api/v2/
```

## Backend Variables

```text
AUTH_ISSUER=https://<auth0-domain>/
AUTH_AUDIENCE=<auth0-api-identifier>
AUTH_JWKS_URL=
AUTH_ALGORITHMS=RS256
AUTH_ACCOUNT_CLAIM=https://edgepilot/account_id
AUTH_ROLE_CLAIM=https://edgepilot/role
AUTH_DEFAULT_ROLE=owner
AUTH0_MANAGEMENT_CLIENT_ID=<m2m-client-id>
AUTH0_MANAGEMENT_CLIENT_SECRET=<m2m-client-secret>
AUTH0_MANAGEMENT_AUDIENCE=https://<auth0-domain>/api/v2/
```

## Frontend Variables

```text
NEXT_PUBLIC_AUTH0_DOMAIN=<auth0-domain>
NEXT_PUBLIC_AUTH0_CLIENT_ID=<spa-client-id>
NEXT_PUBLIC_AUTH0_AUDIENCE=<auth0-api-identifier>
NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://<frontend-domain>
NEXT_PUBLIC_AUTH0_CONNECTION=email
```

For local development, add these Auth0 SPA settings:

- Allowed Callback URLs: `http://localhost:3000`
- Allowed Logout URLs: `http://localhost:3000`
- Allowed Web Origins: `http://localhost:3000`

## Account And Role Claims

If Auth0 does not include `https://edgepilot/account_id`, EdgePilot creates a personal account from the JWT subject.

If Auth0 does not include `https://edgepilot/role`, EdgePilot uses `AUTH_DEFAULT_ROLE`.

For shared accounts, add Auth0 Actions that populate:

```text
https://edgepilot/account_id
https://edgepilot/role
```

## References

- Auth0 access token lifetime: https://auth0.com/docs/secure/tokens/access-tokens/update-access-token-lifetime
- Auth0 refresh token rotation: https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-rotation
- Auth0 passwordless email OTP: https://auth0.com/docs/authenticate/login/auth0-universal-login/passwordless-login/email-or-sms
- Auth0 resend verification emails: https://auth0.com/docs/manage-users/user-accounts/resend-verification-emails
