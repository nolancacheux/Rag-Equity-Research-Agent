# Azure Credentials Setup for GitHub Actions

## Option 1: Azure Portal (Recommended for Students)

1. **Create App Registration**
   - Go to Azure Portal → Azure Active Directory → App registrations
   - Click "New registration"
   - Name: `github-equity-research`
   - Click "Register"

2. **Create Client Secret**
   - In the app, go to "Certificates & secrets"
   - Click "New client secret"
   - Description: `github-actions`
   - Expiry: 12 months
   - Copy the secret value (shown only once!)

3. **Assign Role**
   - Go to your Subscription → Access control (IAM)
   - Click "Add role assignment"
   - Role: `Contributor`
   - Assign access to: "User, group, or service principal"
   - Select: `github-equity-research`

4. **Create GitHub Secret**
   
   Get these values from the App Registration:
   - `clientId`: Application (client) ID
   - `clientSecret`: The secret you created
   - `subscriptionId`: Your subscription ID
   - `tenantId`: Directory (tenant) ID

   Create JSON:
   ```json
   {
     "clientId": "<app-id>",
     "clientSecret": "<secret>",
     "subscriptionId": "8369d09d-46be-4de9-bc4b-fb998edecc74",
     "tenantId": "19e51c11-d919-4a98-899d-9b9dc33f4e04"
   }
   ```

   Then run:
   ```bash
   gh secret set AZURE_CREDENTIALS < credentials.json
   rm credentials.json  # Delete immediately!
   ```

## Option 2: Azure CLI (if you have permissions)

```bash
# Create Service Principal
az ad sp create-for-rbac \
  --name "github-equity-research" \
  --role contributor \
  --scopes /subscriptions/8369d09d-46be-4de9-bc4b-fb998edecc74 \
  --json-auth

# Copy the JSON output, then:
gh secret set AZURE_CREDENTIALS
# Paste the JSON and press Ctrl+D
```

## Option 3: Federated Credentials (Most Secure)

No secrets stored - uses OIDC trust.

1. Create App Registration (same as Option 1, step 1)
2. Go to "Certificates & secrets" → "Federated credentials"
3. Add credential:
   - Scenario: "GitHub Actions deploying Azure resources"
   - Organization: `your-github-username`
   - Repository: `equity-research-agent`
   - Entity: `Branch`
   - Branch: `main`
4. Update workflow to use OIDC (see Azure docs)

## Verify

```bash
# Check secret exists
gh secret list

# Should show:
# AZURE_CREDENTIALS  Updated 2026-01-25
```
