# Staged Vercel Firewall rule: contextual AI

Prepare this as a **separate** custom Vercel Firewall rule. Do not publish it until the
deployment owner approves the draft:

| Setting | Value |
|---|---|
| Name | `Rate limit contextual AI` |
| Match | `POST /api/contextual` |
| Key | Client IP address |
| Limit | 10 requests per 1 minute |
| Action | Return HTTP `429` |

This protects the paid inference endpoint independently of the existing
`POST /api/analyze` rule. The rule is intentionally documented here rather than
published or added to production configuration.
