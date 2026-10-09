# Privacy Policy

**Anakin plugin for Dify**
**Last Updated:** October 9, 2026

Anakin Technologies, Inc. (anakin.io) publishes this plugin. This policy explains
what data the plugin's tools send to Anakin, why, who receives it, how long it is
kept and how you control it. It supplements Anakin's general
[Privacy Policy](https://anakin.io/privacy). Anakin's
[Connectors and Plugins Privacy Policy](https://anakin.io/connector-privacy)
describes the same services and gives the full retention detail.

## How the plugin works

The plugin runs inside your Dify instance. Each tool call sends an HTTPS request
to the Anakin API (`api.anakin.io`) and returns the response to your Dify
workflow or agent. The plugin itself stores nothing: it keeps no database, cache
or log of its own.

## Data We Collect

### Your API key

Your Anakin API key is stored by Dify's credential management and sent with
every request in the `X-API-Key` header. Each request is also tagged
`X-Source: dify` so Anakin can tell plugin traffic apart.

### What you ask the tools to do

The arguments of every tool call, which can include:

- URLs to scrape, map, crawl or monitor, and the options for those requests
- search queries, research prompts and the output schemas you supply
- Wire action inputs, and the website, goal and capabilities for a new Wire action
- browser-task instructions
- questions sent to AI answer engines through AI Visibility
- monitor settings, schedules and alert destinations (webhook URLs and email addresses)

### What the tools return

Page content, structured data extracted from pages, search results, research
answers and their sources, Wire action and build results, browser-task results,
monitor snapshots and detected changes, and the answers AI engines give in AI
Visibility. Content retrieved from websites can contain personal data about other
people. Anakin processes it only to carry out your request.

### Logins for other websites (only if you use them)

- **Wire Login** (`wire_login`): the login details you supply for your own
  account on another site are used to sign in. Anakin keeps the resulting
  session (cookies or tokens), encrypted, and does not store the password. These
  details are a tool argument, so in an agent they pass through the model your
  Dify app uses. To keep a password away from the model, use an identity source
  (a connected password manager or vault) instead.
- **Login builds** (`wire_build` with a Login Credential): the credential is used
  once to sign in while the action is built and is not stored by Anakin. You
  enter it in the tool's settings as a secret field, so the model never sees it;
  Dify stores it with the rest of your app's configuration.
- **Identity sources and saved browser sessions** you set up in the Anakin
  dashboard are stored encrypted by Anakin and referenced by ID from the tools.

### Usage and technical data

For product analytics and troubleshooting, Anakin records the target URL, the
requested country, the calling IP address (your Dify server's), and the type and
outcome of scrape, map, crawl and research requests, plus service logs.

## How We Use It

- To carry out the tool calls you or your agent make, and return the results.
- To authenticate you and apply your plan's credits and limits.
- To run your monitors on schedule and send the alerts you configured.
- To keep the service reliable, troubleshoot problems and improve it.
- To detect and prevent fraud, abuse and security incidents.

Anakin does not use your tool inputs or results to train AI models, and does not
sell your personal information.

## Who Receives It

Depending on the tool, and only as needed to carry out your request or run the
service:

- **The websites you target**, through the proxy country you choose.
- **Web-access providers**: proxy networks, website-unblocking and backup
  scraping services, and CAPTCHA-solving services.
- **Search providers**, which receive your search and research queries.
- **AI model providers**, which receive page content and instructions to extract
  structured data, write research answers, summarize AI Visibility results,
  judge monitored changes, drive browser tasks and build new Wire actions.
- **The AI answer engines you choose in AI Visibility**, which receive your question.
- **Password managers or vaults you connect**, when a login you chose is fetched.
- **Your alert destinations** and the email delivery provider that sends alerts.
- **Analytics, cloud hosting, storage and logging providers** that run the service.

Your Dify instance, and the model provider your Dify app uses, also receive tool
results; they handle them under their own policies.

## How Long We Keep It

- Request records for scrape, map, crawl, search and research: deleted
  automatically after 1 year, or sooner from your dashboard. Retrieved content
  stored for those requests has no fixed expiry; contact us to have it deleted.
- Cached results: up to 24 hours.
- Wire action runs, Wire build requests and AI Visibility searches: no fixed
  expiry; contact us to have them deleted.
- Wire sign-in sessions stop working within 30 days; their record is kept until
  you delete it. Saved browser sessions expire after 90 days without use.
- Monitors, with their check history and detected changes: until you delete the
  monitor. Alert delivery records: 30 days.
- Browser-task status and logs: up to 24 hours.
- Service logs: generally 30 days.

The [Connectors and Plugins Privacy Policy](https://anakin.io/connector-privacy)
lists what deleting your account removes and what it does not.

## Your Controls

- **Remove the plugin or its API key** in Dify at any time, and revoke the key in
  your [Anakin dashboard](https://anakin.io/dashboard).
- **Delete data in the dashboard**: request records, monitors, Wire identities
  and credentials, identity sources, saved browser sessions and API keys. The
  Session Delete and Monitor Control tools also delete sessions and monitors.
- **Access, correction and deletion requests**, including data the dashboard
  cannot delete: email privacy@anakin.io.

## Security

All requests to the Anakin API use HTTPS. API keys, Wire sign-in sessions,
identity-source credentials and saved browser sessions are encrypted at rest. The
plugin does not log request contents.

## Children

The plugin is not intended for anyone under 18.

## Changes to This Policy

We update this policy when what the plugin sends, who receives it or how long it
is kept changes, and change the date above.

## Contact

Anakin Technologies, Inc., 1111B S Governors Ave, STE 25606, Dover, DE 19904, United States

- Privacy and data requests: privacy@anakin.io
- Support: support@anakin.io
