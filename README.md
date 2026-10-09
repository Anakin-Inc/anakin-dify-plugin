# Anakin

**Author:** Anakin
**Version:** 0.1.0
**Type:** Tool Plugin

## Description

Anakin is a web scraping and AI-powered search plugin for Dify. It lets your AI applications extract data from any website, map and crawl sites, run deep research, automate sites through the Wire action catalog, monitor pages for changes, and drive a real cloud browser.

## Key Features

- **Anti-detection** - Proxy routing across 207 countries prevents blocking
- **Intelligent Caching** - Up to 30x faster on repeated requests
- **AI Extraction** - Convert any webpage into structured JSON
- **Browser Automation** - Full Playwright/headless Chrome support for SPAs
- **Session Management** - Authenticated scraping with encrypted session storage (AES-256-GCM)
- **Batch Processing** - Submit multiple URLs in a single request
- **Wire** - Pre-built read and write actions across hundreds of sites, plus on-demand builds for new ones
- **Monitoring** - Scheduled change detection with webhook and email alerts
- **AI Visibility** - Compare how ChatGPT, Gemini and Google AI Overview answer the same question

## Setup

### 1. Get Your API Key

1. Sign up at [anakin.io](https://anakin.io/signup)
2. Go to your [Dashboard](https://anakin.io/dashboard)
3. Copy your API key (starts with `ask_`)

### 2. Configure in Dify

1. Install the Anakin plugin in your Dify workspace
2. Go to **Plugins** → **Anakin** → **Configure**
3. Enter a name for the authorization (e.g., "Production")
4. Paste your API key
5. Click **Save**

## Tools

The plugin has 24 tools. Each tool's parameters are described in Dify when you
add it to a workflow or agent.

### Scrape and search

| Tool | Name | What it does |
|---|---|---|
| URL Scraper | `url_scraper` | Scrape content from a single URL. Returns HTML, cleaned HTML, markdown, and optionally AI-extracted JSON data. |
| Batch URL Scraper | `batch_scraper` | Scrape content from multiple URLs (1-10) in parallel. Returns HTML, cleaned HTML, markdown for each URL. |
| Custom Web Scraper | `web_scraper` | Execute a pre-configured custom scraper to extract structured data from specific websites. |
| AI Search | `search` | AI-powered web search that returns relevant results with URLs, titles, and snippets. |
| Deep Research | `agentic_search` | Launch a 4-stage AI research pipeline that provides comprehensive answers with citations, summaries, and structured data. |

### Map and crawl

| Tool | Name | What it does |
|---|---|---|
| Site Mapper | `map` | Discover all reachable URLs under a given site. Returns internal links, external links, and counts. Useful for understanding a domain's structure before crawling. |
| Site Crawler | `crawl` | Bulk-fetch markdown across a site. Returns an array of pages, each with markdown content and per-page status. Use for catalog ingestion or building a site-wide corpus. |

### Wire: pre-built site actions

| Tool | Name | What it does |
|---|---|---|
| Wire Discover | `wire_discover` | Find Wire actions for a task from a natural-language intent. Wire is Anakin's catalog of pre-built automation actions across hundreds of sites (Amazon, Walmart, LinkedIn, and others). Returns ranked candidate actions with their action_id, type (read/write), params, and cost. |
| Wire Catalog | `wire_catalog` | Browse the Wire catalog. With no slug, lists every supported website and its action count. With a slug, returns that site's full action list with parameter schemas, auth mode, and credit cost. |
| Wire Read Action | `wire_read_action` | Run a Wire READ action — one that extracts data and does not change state on the target site (search listings, get a product's price, read a profile). Polls until the job completes and returns the extracted data. |
| Wire Write Action | `wire_write_action` | Run a Wire WRITE action — one that performs a state-changing interaction on the target site (submit a form, add an item to a cart, update account settings). Polls until the job completes and returns its result. |
| Wire Identities | `wire_identities` | List your saved Wire identities and their credentials. Each credential's id is the credential_id used to run auth-required Wire actions. |
| Wire Login | `wire_login` | Sign in to a credentials-mode Wire site and get a credential_id usable immediately with wire_read_action / wire_write_action. The password is never stored, only the encrypted session. |
| Wire Build | `wire_build` | Request brand-new Wire actions for a website not yet in the catalog, optionally listing the capabilities to build, a proxy country, and a login credential. Wire generates and auto-tests the scrapers, then publishes them. Asynchronous; track progress with Wire Build Status. Charges credits, refunded automatically if the build fails. |
| Wire Build Status | `wire_build_status` | Check on Wire builds started with Wire Build: a build's status, the actions it published, and anything it skipped. Omit the ID to list recent builds. Read-only; spends no credits. |

### Monitoring

| Tool | Name | What it does |
|---|---|---|
| Create Monitor | `monitor_create` | Create a scheduled website monitor that checks a URL periodically and records a change when the content differs, optionally alerting a webhook or email. |
| List Monitors | `monitor_list` | List your website monitors, or pass an id to fetch one monitor's full configuration and status. |
| Monitor Changes | `monitor_changes` | Get the detected changes for a monitor — each entry records when the watched content differed from the previous check, with a diff or summary. |
| Control Monitor | `monitor_control` | Control an existing website monitor: pause, resume, trigger an immediate check, or permanently delete it. |

### AI Visibility

| Tool | Name | What it does |
|---|---|---|
| AI Visibility Search | `ai_visibility_search` | Ask multiple AI answer engines (ChatGPT, Gemini, Google AI Overview) the same question and compare their answers. Returns per-engine results plus an AI-generated synthesis of where they agree and diverge. |
| AI Visibility Sources | `ai_visibility_sources` | List the AI answer engines available to ai_visibility_search, each with its slug and display label. |

### Browser

| Tool | Name | What it does |
|---|---|---|
| Browser Task | `browser_task` | Run a natural-language task in a real cloud browser driven by an AI agent: it navigates, clicks, types, scrolls, and extracts on your behalf. |
| List Sessions | `session_list` | List your saved browser sessions — encrypted login states used for scraping, crawling, monitoring, or browser tasks on authenticated pages. |
| Delete Session | `session_delete` | Permanently delete a saved browser session and its encrypted login data. Irreversible. |

### Building a Wire action for a new site

Wire builds run asynchronously and can take several minutes.

1. Check **Wire Discover** or **Wire Catalog** first. Wire Build is rejected
   with `ACTION_EXISTS` when the site is already covered, unless you set
   **Force**.
2. Call **Wire Build** with the website and a goal. Optionally list the
   **Actions** to build (a JSON array, or one per line), pin a **Country**, or
   set a **Login Credential** to build actions behind a sign-in.
3. Pass the returned `build_request.id` to **Wire Build Status** and poll
   until the status is `success` or `failed`. The result lists the published
   actions with their `action_id`, and a `skipped` list of anything the build
   could not deliver.
4. Run the new actions with **Wire Read Action** or **Wire Write Action**.

The Login Credential is a secret field set in the tool's settings, so the model
never sees it:

```json
{"type": "plain", "username": "me@example.com", "password": "..."}
```

or, for a login stored in a password manager connected to Anakin:

```json
{"type": "vault", "source_id": "...", "source_ref": {"vault_id": "...", "item_id": "..."}}
```

Either form can add `"login_url"` when the sign-in page is not the website URL.
Login builds cost significantly more credits than public builds.

## Usage Examples

### In a Workflow

1. Add a **Tool** node to your workflow
2. Select **Anakin** → Choose your tool
3. Configure parameters:
   - For URL Scraper: Enter the URL, enable `generate_json` for structured output
   - For AI Search: Enter your query
4. Connect to the next node for processing

### In an Agent

1. Create an Agent app
2. Add Anakin tools to the agent's toolset
3. The agent will automatically use scraping/search based on user queries

### Example: Scraping with AI Extraction

```
Tool: URL Scraper
URL: https://example.com/products
Generate JSON: true
```

Returns structured product data automatically extracted by AI.

### Example: Authenticated Scraping

```
Tool: URL Scraper
URL: https://example.com/dashboard
Session ID: your-session-id-from-dashboard
Use Browser: true
```

Scrapes pages that require login using your saved browser session.

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Invalid parameters | Check your input |
| 401 | Invalid API key | Verify your API key |
| 402 | Plan upgrade required | Upgrade your Anakin plan |
| 404 | Job not found | Job may have expired |
| 429 | Rate limit exceeded | Wait and retry |
| 5xx | Server error | Retry with backoff |

## Country Codes

Proxy routing supports 207 countries. Common codes:
- `us` - United States (default)
- `uk` - United Kingdom
- `de` - Germany
- `fr` - France
- `jp` - Japan
- `au` - Australia

## Support

- **Source Code:** [github.com/Anakin-Inc/anakin-dify-plugin](https://github.com/Anakin-Inc/anakin-dify-plugin)
- **Website:** [anakin.io](https://anakin.io)
- **Documentation:** [anakin.io/llms-full.txt](https://anakin.io/llms-full.txt)
- **Dashboard:** [anakin.io/dashboard](https://anakin.io/dashboard)
- **Support:** support@anakin.io

## License

This plugin is provided by Anakin. Usage is subject to Anakin's [Terms of Service](https://anakin.io/terms). See [PRIVACY.md](PRIVACY.md) for what the plugin sends to Anakin and how long it is kept.
