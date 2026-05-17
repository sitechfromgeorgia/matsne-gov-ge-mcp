# Matsne.gov.ge MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🇬🇪 ქართული

### რა არის ეს?

ეს არის **MCP (Model Context Protocol) სერვერი**, რომელიც საშუალებას აძლევს ხელოვნურ ინტელექტს (Claude, VS Code-ის AI ასისტენტები და სხვა) მოძებნოს, წაიკითხოს და გააანალიზოს დოკუმენტები **matsne.gov.ge**-დან — საქართველოს საკანონმდებლო მაცნე.

მაგალითად, შეგიძლიათ სთხოვოთ AI-ს:

- _"მოძებნე დღევანდელი გამოქვეყნებული კანონები"_
- _"მოიძიე დოკუმენტები პერსონალურ მონაცემებზე"_
- _"რა წერია 6840140 ნომერ დოკუმენტში?"_
- _"გააანალიზე ეს კანონი და მომაწოდე რეზიუმე"_

### შესაძლებლობები

| ინსტრუმენტი | რას აკეთებს |
|---|---|
| `matsne_suggest` | სწრაფი ძებნა საკვანძო სიტყვით (ავტომატური დასრულება) |
| `matsne_search` | დოკუმენტების ძებნა ფილტრებით (თარიღი, ტიპი, ორგანო, ნომერი) |
| `matsne_get_document` | დოკუმენტის სრული ინფორმაცია (მეტამონაცემები + ტექსტი + სტრუქტურა) |
| `matsne_get_tree` | დოკუმენტის სტრუქტურის ხე (მუხლები, თავები, ნაწილები) |
| `matsne_get_back_references` | რომელი დოკუმენტები ეყრდნობა/ეხება ამ დოკუმენტს |
| `matsne_get_comments` | დოკუმენტის კომენტარები |
| `matsne_get_linked` | დოკუმენტის კონკრეტული ნაწილის ტექსტი (მაგ., კონკრეტული მუხლი) |
| `matsne_search_by_keyword` | საკვანძო სიტყვით ძებნა (აბრუნებს მხოლოდ აქტიურ დოკუმენტებს) |
| `matsne_has_today` | არის თუ არა დღეს გამოქვეყნებული დოკუმენტები |
| `matsne_today_documents` | დღეს გამოქვეყნებული დოკუმენტების სია |

### მოთხოვნები

- **Python** 3.10 ან უფრო ახალი → [python.org/downloads](https://www.python.org/downloads/)
- **uv** — Python-ის პროექტების მენეჯერი (იხ. ქვემოთ)

### ინსტალაცია (ნაბიჯ-ნაბიჯ)

#### ნაბიჯი 1: Python-ის დაყენება

თუ Python არ გაქვთ დაყენებული:

1. გადადით ბმულზე: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. დააჭირეთ ყვითელ ღილაკს "Download Python"
3. გახსენით ჩამოტვირთული ფაილი
4. **მნიშვნელოვანი:** მონიშნეთ "Add Python to PATH" (ბოლოში)
5. დააჭირეთ "Install Now"

#### ნაბიჯი 2: uv-ის დაყენება

**Windows-ზე:** გახსენით PowerShell (დააჭირეთ Windows ღილაკს, ჩაწერეთ "PowerShell" და გახსენით), ჩაწერეთ:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac/Linux-ზე:** გახსენით ტერმინალი და ჩაწერეთ:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

დაყენების შემდეგ გადატვირთეთ ტერმინალი/ფანჯარა.

#### ნაბიჯი 3: პროექტის ჩამოტვირთვა

**Git-ით (თუ იცნობთ):**
```sh
git clone https://github.com/YOUR_USERNAME/matsne-gov-ge-mcp
cd matsne-gov-ge-mcp
```

**ZIP-ით (მარტივი გზა):**
1. გადადით GitHub გვერდზე
2. დააჭირეთ ღილაკს "Code" → "Download ZIP"
3. გახსენით ZIP ფაილი
4. გადადით გახსნილ საქაღალდეში

#### ნაბიჯი 4: MCP სერვერის გაშვება

გახსენით ტერმინალი/კონსოლი პროექტის საქაღალდეში და ჩაწერეთ:

```sh
uv run mcp_server.py
```

თუ ყველაფერი სწორადაა, ვერაფერს დაინახავთ — ეს ნორმალურია, სერვერი მუშაობს ფონზე. გამოსასვლელად დააჭირეთ `Ctrl+C`.

### Claude Desktop-ში გამოყენება

1. გახსენით **Claude Desktop**
2. დააჭირეთ Settings (პარამეტრები) → Developer (დეველოპერი)
3. **Edit Config**-ში ჩასვით ეს კონფიგურაცია:

```json
{
  "mcpServers": {
    "matsne-ge": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\თქვენი_მომხმარებელი\\matsne-gov-ge-mcp", "run", "mcp_server.py"]
    }
  }
}
```

**მნიშვნელოვანი:** `C:\\Users\\თქვენი_მომხმარებელი\\...` — შეცვალეთ იმ გზით, სადაც პროექტი ჩამოტვირთეთ.

მაგალითად, თუ ჩამოტვირთეთ დესკტოპზე:

```json
{
  "mcpServers": {
    "matsne-ge": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\ირაკლი\\Desktop\\matsne-gov-ge-mcp", "run", "mcp_server.py"]
    }
  }
}
```

4. გადატვირთეთ Claude Desktop
5. თუ ზედა მარცხენა კუთხეში გამოჩნდება 🔧 (ხელის ხატულა), მიმაგრებულია წარმატებით

### ინსტრუქციის მაგალითები

შეგიძლიათ სცადოთ ეს მოთხოვნები Claude-ში:

- _"მოძებნე დღევანდელი გამოქვეყნებული დოკუმენტები matsne.gov.ge-დან"_
- _"მოიძიე კანონები შრომის შესახებ, რომელიც ბოლო 30 დღეში გამოქვეყნდა"_
- _"რა წერია დოკუმენტში #6840140? გააანალიზე"_
- _"მომაწოდე ინფორმაცია 6840140 დოკუმენტზე: ვინ მიიღო, როდის გამოქვეყნდა, ტიპი"_
- _"მოძებნე 'პერსონალური მონაცემები' და მომაწოდე აქტიური კანონების სია"_

### Troubleshooting

| პრობლემა | გამოსავალი |
|---|---|
| "uv is not recognized" | uv არ დაყენებულა → გადახედეთ ნაბიჯ 2-ს. გადატვირთეთ ტერმინალი. |
| "Python not found" | Python არ დაყენებულა → python.org-დან ჩამოტვირთეთ. დარწმუნდით რომ "Add to PATH" მონიშნეთ. |
| "No module named mcp" | გაუშვით `uv run mcp_server.py` (uv ავტომატურად დააყენებს ყველაფერს) |
| Claude-ში 🔧 არ ჩანს | შეამოწმეთ JSON config-ში ბილიკი სწორია თუ არა |
| "Access Denied" matsne-დან | API endpoint-ები მუშაობს, ეს მხოლოდ HTML გვერდის ბლოკირებაა. `get_document()` მაინც მიიღებს ტექსტს linked fragments-ის მეშვეობით. |

---

## 🇬🇧 English

### What is this?

An **MCP (Model Context Protocol) server** for [matsne.gov.ge](https://matsne.gov.ge) — Georgia's official legislative database. It lets AI assistants (Claude Desktop, VS Code, etc.) search, read, and analyze Georgian legislation through a simple API.

### Features

| Tool | Description |
|---|---|
| `matsne_suggest` | Fast keyword autocomplete search |
| `matsne_search` | Full-text search with filters (date, type, organ, number) |
| `matsne_get_document` | Full document: metadata + text + structure + back-references + comments |
| `matsne_get_tree` | Document structure tree (articles, chapters, parts) |
| `matsne_get_back_references` | Which documents cite or reference this document |
| `matsne_get_comments` | User comments on a document |
| `matsne_get_linked` | Text of a specific document part (e.g., a specific article) |
| `matsne_search_by_keyword` | Keyword search returning only active documents |
| `matsne_has_today` | Check if documents were published today |
| `matsne_today_documents` | List today's published documents |
| `matsne://document/{id}` (resource) | Document as structured JSON data |
| `matsne://today` (resource) | Today's documents as JSON |

### Requirements

- **Python** 3.10+ → [python.org/downloads](https://www.python.org/downloads/)
- **uv** — Python project manager (see installation below)

### Installation

#### Step 1: Install Python

Download from [python.org/downloads](https://www.python.org/downloads/). **Important on Windows:** check "Add Python to PATH" during installation.

#### Step 2: Install uv

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac/Linux:**
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installation.

#### Step 3: Download the project

```sh
git clone https://github.com/YOUR_USERNAME/matsne-gov-ge-mcp
cd matsne-gov-ge-mcp
```

Or download as ZIP from GitHub and extract.

#### Step 4: Run the MCP server

```sh
uv run mcp_server.py
```

The server runs silently in the background (stdio mode). Press `Ctrl+C` to stop.

### Claude Desktop Configuration

1. Open **Claude Desktop** → Settings → Developer → Edit Config
2. Add this configuration (update the path to your project folder):

```json
{
  "mcpServers": {
    "matsne-ge": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\YOUR_USERNAME\\matsne-gov-ge-mcp", "run", "mcp_server.py"]
    }
  }
}
```

3. Restart Claude Desktop
4. You should see a 🔧 (wrench icon) in the top-left corner when connected

### Example Prompts

Try asking Claude:

- _"Search for today's published documents on matsne.gov.ge"_
- _"Find laws about personal data published in the last month"_
- _"Get full information on document #6840140 and summarize it"_
- _"What documents were published today?"_

### Troubleshooting

| Problem | Solution |
|---|---|
| "uv is not recognized" | uv not installed → reinstall and restart terminal |
| "Python not found" | Install Python with "Add to PATH" checked |
| "No module named mcp" | Always use `uv run mcp_server.py` (not plain `python`) |
| Claude doesn't show wrench icon | Check the path in your JSON config |

---

## License

[MIT](LICENSE) — use it freely, share it, improve it.

---

შექმნილია სიყვარულით ბათუმიდან <3  
Made with love from Batumi <3
