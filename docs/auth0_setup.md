# Auth0 傻瓜配置指南

这份文档按“第一次用 Auth0”的方式写。当前默认方案是最简单、最稳的：

```text
邮箱 + 密码登录
```

先不做邮箱一次性验证码，也不碰 `Identifier First`。这样可以绕开 Auth0 Dashboard 里 New/Classic Universal Login 的复杂限制。

目标：

- 用户必须登录才能用 EdgePilot。
- 登录方式先用邮箱 + 密码。
- access token 有效期 30 分钟。
- refresh token 最长 24 小时，前端自动刷新 access token。
- refresh token 过期后用户需要重新登录。
- 未验证邮箱的用户不能进入工作台。

## 0. 先准备 3 个名字

为了不绕，建议先用下面这组名字：

```text
Frontend App name: EdgePilot Frontend
Backend API name: EdgePilot API
API Identifier: https://edgepilot-api
Machine App name: EdgePilot Backend Management
Database Connection name: Username-Password-Authentication
```

`Username-Password-Authentication` 通常是 Auth0 默认创建的数据库连接。如果你的 Auth0 里没有它，也可以自己创建一个，名字用：

```text
EdgePilot Database
```

后面看到 `<auth0-domain>`，意思是你的 Auth0 域名，例如：

```text
dev-xxxxxx.au.auth0.com
```

不要把尖括号 `< >` 一起复制进去。

## 1. 注册 / 登录 Auth0

1. 打开 Auth0 Dashboard。
2. 如果还没有账号，先注册。
3. 进入你的 Tenant。
4. 记住 Domain，例如：

```text
dev-xxxxxx.au.auth0.com
```

这个值后面会填到：

```text
NEXT_PUBLIC_AUTH0_DOMAIN=dev-xxxxxx.au.auth0.com
AUTH_ISSUER=https://dev-xxxxxx.au.auth0.com/
AUTH0_MANAGEMENT_AUDIENCE=https://dev-xxxxxx.au.auth0.com/api/v2/
```

注意：

- `NEXT_PUBLIC_AUTH0_DOMAIN` 不要加 `https://`。
- `AUTH_ISSUER` 要加 `https://`，最后还要有 `/`。
- `AUTH0_MANAGEMENT_AUDIENCE` 要以 `/api/v2/` 结尾。

## 2. 创建后端 API

左侧菜单：

```text
Applications -> APIs -> Create API
```

填写：

```text
Name: EdgePilot API
Identifier: https://edgepilot-api
Signing Algorithm: RS256
```

创建后，进入这个 API 的 `Settings` 页面。

找到 token 过期时间，填：

```text
Maximum Access Token Lifetime: 1800
```

`1800` 秒就是 30 分钟。

如果下面还有这个字段，也填 `1800`：

```text
Implicit / Hybrid Flow Access Token Lifetime: 1800
```

这个字段默认可能是 `7200`。它不能大于上面的 `Maximum Access Token Lifetime`，否则 Auth0 会报：

```text
token_lifetime_for_web cannot be larger than token_lifetime
```

如果看到 `Allow Offline Access`，打开它。这个是 refresh token 需要的。

保存。

还要授权前端应用访问这个 API，否则登录时会报：

```text
Client "<client_id>" is not authorized to access resource server "https://edgepilot-api"
```

左侧菜单：

```text
Applications -> APIs -> EdgePilot API -> Application Access
```

先看 `User Access`。第一版最省心的设置是：

```text
User Access Policy: Allow
```

保存。

如果你的 Auth0 页面没有 `Allow`，只有 `Allow via client-grant`，就找到 `EdgePilot Frontend`，把它的 `User Access` 授权打开：

```text
EdgePilot Frontend: Authorized / All
```

保存。

## 3. 创建前端应用

左侧菜单：

```text
Applications -> Applications -> Create Application
```

填写：

```text
Name: EdgePilot Frontend
Application type: Single Page Application
```

创建后进入 `Settings`。

复制这两个值，后面会用：

```text
Domain
Client ID
```

这一页字段很多，第一版只需要关心这些：

```text
Name: EdgePilot Frontend
Domain: 复制到 NEXT_PUBLIC_AUTH0_DOMAIN
Client ID: 复制到 NEXT_PUBLIC_AUTH0_CLIENT_ID
Client Secret: 不要复制到 frontend，也不要放进 Git
Application Type: Single Page Application
Application Login URI: 先留空
Allowed Callback URLs: http://localhost:3000
Allowed Logout URLs: http://localhost:3000
Allowed Web Origins: http://localhost:3000
Allowed Origins (CORS): 先留空
```

如果你的 Auth0 页面显示：

```text
Domain: dev-xxxxxx.au.auth0.com
Client ID: xxxxx
```

那么 `frontend/.env.local` 里就是：

```text
NEXT_PUBLIC_AUTH0_DOMAIN=dev-xxxxxx.au.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=xxxxx
```

注意：这个前端 App 里的 `Client Secret` 不要用。Single Page Application 跑在浏览器里，不能保存 secret。

在同一个 `Settings` 页面往下找，填本地开发地址：

```text
Allowed Callback URLs:
http://localhost:3000

Allowed Logout URLs:
http://localhost:3000

Allowed Web Origins:
http://localhost:3000
```

如果已经部署了前端，也把正式前端域名加进去，例如：

```text
https://your-frontend.vercel.app
```

保存。

## 4. 打开 Refresh Token Rotation

还是在 `EdgePilot Frontend` 这个应用里。

左侧/页面位置大概是：

```text
Applications -> Applications -> EdgePilot Frontend -> Settings
```

往下找 `Refresh Token Rotation`。

打开：

```text
Allow Refresh Token Rotation: On
```

然后设置：

```text
Set Maximum Refresh Token Lifetime: On
Maximum Refresh Token Lifetime: 86400
```

`86400` 秒就是 24 小时。

`Set Idle Refresh Token Lifetime` 推荐先关掉。我们第一版真正需要的是“refresh token 最多活 24 小时”，这个由上面的 `Maximum Refresh Token Lifetime` 保证。

如果 Auth0 页面一定要求你打开 Idle，或者你已经打开了它，就这样填：

```text
Set Idle Refresh Token Lifetime: On
Idle Refresh Token Lifetime: 82800
```

`82800` 秒是 23 小时。Auth0 要求 Idle 必须小于 Maximum，所以这里不能填 `86400`。

如果看到 Grant Types 或 Advanced Settings，确认启用：

```text
Authorization Code
Refresh Token
```

保存。

## 5. 打开邮箱 + 密码登录

左侧菜单：

```text
Authentication -> Database
```

先看看有没有这个连接：

```text
Username-Password-Authentication
```

如果有，点进去。

如果没有，点 `Create DB Connection`，填写：

```text
Name: EdgePilot Database
```

创建后，进入这个 Database connection。

在 `Applications` tab 里，把前端应用打开：

```text
EdgePilot Frontend: On
```

第一版推荐不要强制 username，直接用邮箱 + 密码：

```text
Requires Username: Off
```

这样用户登录和注册时用邮箱地址，不需要额外记一个 username。

如果你想让用户可以用 username 登录，以后再打开 `Requires Username`。Auth0 文档里说，打开后新用户注册时需要填 username 和 email，之后可以用 username 或 email 登录。这个会多一步，先不建议。

如果页面有密码强度设置，建议先选中等或强：

```text
Password Strength: Good / Excellent
```

保存。

## 6. 不需要配置 Passwordless

这条路线不需要：

```text
Authentication -> Passwordless -> Email
Authentication -> Authentication Profile -> Identifier First
```

也就是说，之前卡住你的 `Identifier First` 可以先完全不管。

前端环境变量里也不要填：

```text
NEXT_PUBLIC_AUTH0_CONNECTION=email
```

保持空值即可：

```text
NEXT_PUBLIC_AUTH0_CONNECTION=
```

这样前端不会强制指定 passwordless email connection，Auth0 会使用你给 `EdgePilot Frontend` 启用的 Database connection。

## 7. 创建后端 Management 应用

这个应用不是给用户登录用的。它是给 EdgePilot 后端调用 Auth0，用来：

- 重发邮箱验证邮件。
- 在 access token 没有 `email_verified` 字段时，查询用户是否已经验证邮箱。

左侧菜单：

```text
Applications -> Applications -> Create Application
```

填写：

```text
Name: EdgePilot Backend Management
Application type: Machine to Machine Applications
```

创建时 Auth0 会让你选择 API。

选择：

```text
Auth0 Management API
```

勾选权限：

```text
read:users
update:users
```

保存。

进入这个 Machine to Machine 应用的 `Settings` 页面，复制：

```text
Client ID
Client Secret
```

后面填到：

```text
AUTH0_MANAGEMENT_CLIENT_ID=
AUTH0_MANAGEMENT_CLIENT_SECRET=
```

## 8. 本地 `.env` 怎么填

根目录 `.env` 或 `backend/.env` 填：

```text
AUTH_ISSUER=https://dev-xxxxxx.au.auth0.com/
AUTH_AUDIENCE=https://edgepilot-api
AUTH_JWKS_URL=
AUTH_ALGORITHMS=RS256
AUTH_ACCOUNT_CLAIM=https://edgepilot/account_id
AUTH_ROLE_CLAIM=https://edgepilot/role
AUTH_EMAIL_CLAIM=https://edgepilot/email
AUTH_DISPLAY_NAME_CLAIM=https://edgepilot/name
AUTH_EMAIL_VERIFIED_CLAIM=https://edgepilot/email_verified
AUTH_DEFAULT_ROLE=owner

AUTH0_MANAGEMENT_CLIENT_ID=<EdgePilot Backend Management 的 Client ID>
AUTH0_MANAGEMENT_CLIENT_SECRET=<EdgePilot Backend Management 的 Client Secret>
AUTH0_MANAGEMENT_AUDIENCE=https://dev-xxxxxx.au.auth0.com/api/v2/
```

`frontend/.env.local` 填：

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SSE_URL=http://localhost:8000/api/realtime/events/stream
NEXT_PUBLIC_APP_NAME=EdgePilot

NEXT_PUBLIC_AUTH0_DOMAIN=dev-xxxxxx.au.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=<EdgePilot Frontend 的 Client ID>
NEXT_PUBLIC_AUTH0_AUDIENCE=https://edgepilot-api
NEXT_PUBLIC_AUTH0_REDIRECT_URI=http://localhost:3000
NEXT_PUBLIC_AUTH0_CONNECTION=
```

注意：

- `AUTH_AUDIENCE` 和 `NEXT_PUBLIC_AUTH0_AUDIENCE` 必须完全一样。
- `NEXT_PUBLIC_AUTH0_CONNECTION` 先留空。
- `AUTH0_MANAGEMENT_CLIENT_SECRET` 绝对不要放到 frontend。

## 9. Railway 怎么填

Railway 后端服务 Variables 填：

```text
AUTH_ISSUER=https://dev-xxxxxx.au.auth0.com/
AUTH_AUDIENCE=https://edgepilot-api
AUTH_JWKS_URL=
AUTH_ALGORITHMS=RS256
AUTH_ACCOUNT_CLAIM=https://edgepilot/account_id
AUTH_ROLE_CLAIM=https://edgepilot/role
AUTH_EMAIL_CLAIM=https://edgepilot/email
AUTH_DISPLAY_NAME_CLAIM=https://edgepilot/name
AUTH_EMAIL_VERIFIED_CLAIM=https://edgepilot/email_verified
AUTH_DEFAULT_ROLE=owner
AUTH0_MANAGEMENT_CLIENT_ID=<EdgePilot Backend Management 的 Client ID>
AUTH0_MANAGEMENT_CLIENT_SECRET=<EdgePilot Backend Management 的 Client Secret>
AUTH0_MANAGEMENT_AUDIENCE=https://dev-xxxxxx.au.auth0.com/api/v2/
```

前端部署平台，例如 Vercel 或 Railway frontend，填：

```text
NEXT_PUBLIC_AUTH0_DOMAIN=dev-xxxxxx.au.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=<EdgePilot Frontend 的 Client ID>
NEXT_PUBLIC_AUTH0_AUDIENCE=https://edgepilot-api
NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://<你的前端域名>
NEXT_PUBLIC_AUTH0_CONNECTION=
```

然后回到 Auth0 的 `EdgePilot Frontend` 应用，把正式域名也加到：

```text
Allowed Callback URLs
Allowed Logout URLs
Allowed Web Origins
```

## 10. 怎么验证配置成功

本地启动：

```bash
uvicorn backend.app.main:app --reload --port 8000
cd frontend
npm run dev -- --port 3000
```

打开：

```text
http://localhost:3000
```

应该看到登录入口。

点击登录后：

1. 跳到 Auth0。
2. 看到邮箱 + 密码登录页。
3. 如果没有账号，点注册/Sign up。
4. 注册后回到 EdgePilot。
5. 如果邮箱还没验证，会看到验证提示页。

点击：

```text
Resend verification email
```

然后去邮箱点激活链接。点完后回到 EdgePilot，点击：

```text
I verified my email
```

## 11. 最容易填错的地方

### 登录后回不来

检查 Auth0 `Allowed Callback URLs` 里有没有：

```text
http://localhost:3000
```

部署后还要有：

```text
https://<你的前端域名>
```

### API 一直 401

检查：

```text
AUTH_AUDIENCE
NEXT_PUBLIC_AUTH0_AUDIENCE
```

这两个必须完全一样。

还要检查前端 App 是否被授权访问 API：

```text
Applications -> APIs -> EdgePilot API -> Application Access
```

推荐：

```text
User Access Policy: Allow
```

或者授权：

```text
EdgePilot Frontend: Authorized / All
```

如果没有这一步，Auth0 登录会跳回前端，并带上：

```text
Client "<client_id>" is not authorized to access resource server "https://edgepilot-api"
```

### API 报 issuer 错误

检查：

```text
AUTH_ISSUER=https://dev-xxxxxx.au.auth0.com/
```

它必须：

- 有 `https://`
- 结尾有 `/`

### 保存 API 时报 token_lifetime_for_web 错误

这是因为：

```text
Implicit / Hybrid Flow Access Token Lifetime
```

比：

```text
Maximum Access Token Lifetime
```

更大。

解决方法很简单：两个都填 `1800`。

### 保存前端 App 时报 Inactivity Lifetime 错误

如果你看到：

```text
"Inactivity Lifetime" must be less than 86400
```

这是因为你把：

```text
Idle Refresh Token Lifetime
```

也填成了 `86400`。Auth0 要求 Idle 必须小于 Maximum。

推荐做法：

```text
Set Idle Refresh Token Lifetime: Off
Set Maximum Refresh Token Lifetime: On
Maximum Refresh Token Lifetime: 86400
```

如果必须填 Idle，就填：

```text
Idle Refresh Token Lifetime: 82800
```

### 登录页还是显示一次性验证码

检查：

```text
frontend/.env.local
```

确认：

```text
NEXT_PUBLIC_AUTH0_CONNECTION=
```

不要填 `email`。

然后重启前端：

```bash
cd frontend
npm run dev -- --port 3000
```

### 登录页没有邮箱 + 密码

检查 Database connection 有没有启用给前端应用：

```text
Authentication -> Database -> Username-Password-Authentication -> Applications
```

确认：

```text
EdgePilot Frontend: On
```

### 重发验证邮件失败

检查 Machine to Machine 应用是否授权了：

```text
Auth0 Management API
read:users
update:users
```

还要检查：

```text
AUTH0_MANAGEMENT_CLIENT_ID
AUTH0_MANAGEMENT_CLIENT_SECRET
AUTH0_MANAGEMENT_AUDIENCE
```

### 已经验证邮箱但工作台 API 还是 403

这通常是因为后端拿到的 API access token 里没有 `email_verified`。当前代码会自动去 Auth0 Management API 查用户资料，所以 Machine to Machine 应用必须授权：

```text
read:users
```

路径：

```text
Applications -> APIs -> Auth0 Management API -> Machine to Machine Applications
```

找到：

```text
EdgePilot Backend Management
```

勾选并保存：

```text
read:users
update:users
```

## 12. 先不要管的高级内容

下面这些以后再做，不影响第一版登录：

- 邮箱一次性验证码 passwordless。
- Identifier First。
- 多人共享一个 account。
- Auth0 Actions 自动写 `account_id` 和 `role`。
- 更复杂的角色权限。
- MFA。

现在第一版默认策略是：

- 每个 Auth0 用户自动拥有自己的个人 account。
- 如果 token 里没有 role，默认是 `owner`。

## References

- Auth0 database connections: https://auth0.com/docs/authenticate/database-connections
- Auth0 set up database connections: https://auth0.com/docs/get-started/applications/set-up-database-connections
- Auth0 username for database connections: https://auth0.com/docs/authenticate/database-connections/require-username
- Auth0 password policies: https://auth0.com/docs/authenticate/database-connections/password-options
- Auth0 access token lifetime: https://auth0.com/docs/secure/tokens/access-tokens/update-access-token-lifetime
- Auth0 refresh token rotation: https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-rotation
- Auth0 resend verification emails: https://auth0.com/docs/manage-users/user-accounts/resend-verification-emails
