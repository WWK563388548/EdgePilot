export type AuthMe = {
  user_id: string;
  account_id: string;
  tenant_id: string;
  role: string;
  email: string | null;
  display_name: string | null;
  email_verified: boolean;
};

export type Tenant = {
  tenant_id: string;
  name: string;
  slug: string | null;
  owner_user_id: string | null;
  status: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type TenantMember = {
  tenant_id: string;
  user_id: string;
  role: string;
  email: string | null;
  display_name: string | null;
  created_at: string | null;
};

export type TenantApiKey = {
  credential_id: string;
  tenant_id: string;
  provider: string;
  label: string | null;
  status: string | null;
  key_fingerprint: string | null;
  has_encrypted_payload: boolean;
  last_verified_at: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type TenantApiKeyCreate = {
  provider: string;
  label?: string | null;
  encrypted_payload?: string | null;
  key_fingerprint?: string | null;
  metadata_json?: Record<string, unknown> | null;
};

export type TenantDataCapability = {
  capability_id: string;
  tenant_id: string;
  capability_key: string;
  provider: string | null;
  market: string | null;
  asset_type: string | null;
  timeframe: string | null;
  status: string;
  source: string | null;
  reason: string | null;
  last_checked_at: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type DataSourceCheckResponse = {
  provider: string;
  capability_key: string;
  status: string;
  source: string | null;
  message: string | null;
  checked_at: string;
  credential_id: string | null;
};

export type VerificationEmailResponse = {
  status: string;
  job_id: string | null;
};
