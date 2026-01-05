# Rejestr.io MCP Server

A Model Context Protocol (MCP) server providing access to Poland's largest business registry database - rejestr.io.

## 📋 What is this?

This MCP server enables AI assistants and applications to:
- 🔍 Search companies by name, NIP (Tax ID), or KRS (Court Register)
- 🏢 Retrieve detailed company information
- 👥 Check real beneficiaries from CRBR (Central Register of Real Beneficiaries)
- 🔗 Analyze connections between companies and individuals
- 📊 Access financial documents and statements
- 📄 Browse KRS (National Court Register) records

## 🎯 Choose Your Setup

**👤 Are you a Claude Desktop user?** → [Jump to Claude Desktop Setup](#-for-claude-desktop-users)

**👨‍💻 Are you a developer/want local control?** → [Jump to Developer Setup](#-for-developers--local-usage)

---

## 👤 For Claude Desktop Users

> This section is for non-technical users who want to use this MCP server with Claude Desktop app.

### Step 1: Get rejestr.io API Key

1. Register at [rejestr.io](https://rejestr.io/)
2. Purchase an API plan (various options available)
3. Copy your API key from the user panel

### Step 2: Install Python

1. Download Python 3.13 or newer from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation by opening terminal and typing:
   ```bash
   python --version
   ```

### Step 3: Download and Configure Server

1. Download this repository (green "Code" button → "Download ZIP") and extract it
2. Create a `.env` file in the main project folder with your API key:
   ```
   REJESTR_IO_API_KEY=your_api_key_here
   ```

### Step 4: Configure Claude Desktop

1. Open Claude Desktop config file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add this configuration (replace `PATH_TO_PROJECT` with full path to project folder):

   **Windows:**
   ```json
   {
     "mcpServers": {
       "rejestr-io": {
         "command": "python",
         "args": ["-m", "rejestr_io_mcp"],
         "cwd": "C:\\Users\\YourName\\rejestr-io-mcp",
         "env": {
           "PYTHONPATH": "C:\\Users\\YourName\\rejestr-io-mcp"
         }
       }
     }
   }
   ```

   **macOS/Linux:**
   ```json
   {
     "mcpServers": {
       "rejestr-io": {
         "command": "python3",
         "args": ["-m", "rejestr_io_mcp"],
         "cwd": "/home/your_name/rejestr-io-mcp",
         "env": {
           "PYTHONPATH": "/home/your_name/rejestr-io-mcp"
         }
       }
     }
   }
   ```

3. Save the file and restart Claude Desktop

### Step 5: Test It

Open Claude Desktop and ask:
```
Check my rejestr.io account balance
```

If everything works correctly, Claude should return your account balance information.

### 🐛 Troubleshooting (Claude Desktop)

**Claude doesn't see the tools:**
1. Verify paths in `claude_desktop_config.json` are correct
2. Make sure `.env` file contains valid API key
3. Restart Claude Desktop completely

**Authorization error:**
1. Check if API key in `.env` is correct
2. Verify your API plan is active at rejestr.io
3. Check account balance

**Import errors:**
1. Ensure Python is installed correctly
2. Check Python version: `python --version` (requires 3.13+)
3. Try reinstalling: `pip install httpx python-dotenv mcp`

---

## 👨‍💻 For Developers / Local Usage

> This section is for developers who want to integrate this MCP server with custom agents, applications, or use it locally.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-user/rejestr-io-mcp.git
cd rejestr-io-mcp

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -e .

# Create .env file with your API key
echo "REJESTR_IO_API_KEY=your_api_key_here" > .env
```

### Local Testing

```bash
# Run server in stdio mode
python -m rejestr_io_mcp

# Use MCP Inspector for interactive testing
npx @modelcontextprotocol/inspector python -m rejestr_io_mcp
```

### Integration with Custom Agents

The server communicates via stdio using the Model Context Protocol. Example integration:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_agent():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "rejestr_io_mcp"],
        env={"REJESTR_IO_API_KEY": "your_key_here"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool(
                "get_company_info_using_nip",
                arguments={"nip": "5252408074"}
            )
            print(result)

asyncio.run(run_agent())
```

### Project Structure

```
rejestr-io-mcp/
├── rejestr_io_mcp.py      # Main MCP server implementation
├── pyproject.toml          # Project configuration & dependencies
├── .gitignore             # Git ignore file
└── README.md              # This documentation
```

### Environment Variables

- `REJESTR_IO_API_KEY` (required) - Your rejestr.io API key

### Dependencies

- Python 3.13+
- httpx >= 0.28.1 - Async HTTP client
- mcp >= 1.25.0 - Model Context Protocol SDK
- python-dotenv - Environment variable management

### API Endpoints Used

All endpoints use `https://rejestr.io/api/v2` base URL:
- `GET /org?nazwa={name}` - Search companies
- `GET /org/{krs}` - Get company by KRS
- `GET /org/nip/{nip}` - Get company by NIP
- `GET /org/{krs}/crbr` - Get beneficiaries
- `GET /org/{krs}/krs-powiazania` - Get company connections
- `GET /osoby/{id}` - Get person data
- `GET /osoby/{id}/krs-powiazania` - Get person connections
- `GET /org/{krs}/krs-rozdzialy/{chapter}` - Get KRS chapter
- `GET /org/{krs}/krs-dokumenty` - List financial documents
- `GET /org/{krs}/krs-dokumenty/{doc_id}?format=json` - Get financial statement (costs 0.50 PLN)
- `GET /konto/stan` - Check account balance

### Adding to Other MCP Clients

**For Cline (VSCode extension):**
Add to your VSCode settings:
```json
{
  "mcp.servers": {
    "rejestr-io": {
      "command": "python",
      "args": ["-m", "rejestr_io_mcp"],
      "cwd": "/path/to/rejestr-io-mcp"
    }
  }
}
```

**For custom applications:**
Use the MCP SDK to connect to the server via stdio transport.

---

## 🛠️ Available Tools

### Company Search

- **`get_company_info_using_name`** - Search company by name
  ```
  Find information about "CD Projekt" company
  ```

- **`get_company_info_using_nip`** - Get company data by NIP (Tax ID)
  ```
  Show company with NIP 5252408074
  ```

- **`get_company_info_using_krs`** - Get company data by KRS number
  ```
  What are the details of company KRS 0000012345?
  ```

### Detailed Information

- **`get_company_krs_documentation`** - Get specific KRS chapter
  - Available chapters: `ogolny`, `oddzialy`, `akcje`, `wzmianki`, `zobowiazania`, `przeksztalcenia`
  ```
  Show general chapter from KRS for company 0000012345
  ```

- **`get_person_data`** - Get person information
  ```
  Show data for person ID 123456
  ```

### Beneficiaries and Connections

- **`get_beneficiary`** - List of real beneficiaries from CRBR
  ```
  Who is the beneficiary of company KRS 0000012345?
  ```

- **`get_connections_by_krs`** - Company connections
  ```
  Show all connections for company KRS 0000012345
  ```

- **`get_connections_by_person`** - Person connections
  ```
  In which companies does person ID 123456 operate?
  ```

### Financial Documents

- **`get_financial_documents`** - List of financial documents
  ```
  Show available financial statements for KRS 0000012345
  ```

- **`get_financial_statement_in_json`** - Download statement (costs 0.50 PLN)
  ```
  Download financial statement document ID 789 for KRS 0000012345
  ```

### Account Management

- **`get_token_amount`** - Check account balance
  ```
  How much credit do I have on my rejestr.io account?
  ```

## 💡 Usage Examples

### Company Analysis
```
Find "Allegro" company and show:
1. Basic information
2. Real beneficiaries
3. All connections with other companies
```

### Due Diligence
```
For company KRS 0000012345 check:
- Is it in liquidation or bankruptcy
- Who is the real beneficiary
- What connections it has with other entities
- Latest financial statements
```

### Person Analysis
```
Find Jan Kowalski in company X, then show all companies 
where this person holds any position
```

## 📝 Important Notes

- ⚠️ **Costs**: Downloading financial statements in JSON costs 0.50 PLN per document, rest operations are cost per usage.
- 🔐 **Security**: Never share your API key. The `.env` file should be in `.gitignore`
- 📊 **Limits**: Check your API plan limits at rejestr.io
- 🔄 **Updates**: Data in rejestr.io is regularly updated from official registries

## 📚 Additional Resources

- [rejestr.io API Documentation](https://rejestr.io/api/info/wyszukiwanie-organizacji)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Desktop Documentation](https://claude.ai/desktop)

## 📄 License

MIT License - feel free to use, modify, and distribute this code.

## 🤝 Contributing

Bug reports and pull requests are welcome!

---

Made with ❤️ for the Polish business data community
