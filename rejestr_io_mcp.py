"""
Rejestr.io MCP Server

This Model Context Protocol (MCP) server provides tools for accessing the rejestr.io API,
which offers access to Polish business registry data including KRS, NIP, REGON,
Central Register of Real Beneficiaries (CRBR), and financial documents.

API Documentation: https://rejestr.io/api/info/wyszukiwanie-organizacji
"""

from typing import Any
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server for Model Context Protocol communication
mcp = FastMCP("rejestr_io_mcp")

# Configure API authentication headers with the API key from environment
headers = {'Authorization': os.getenv("REJESTR_IO_API_KEY")}

# Base URL for all rejestr.io API v2 endpoints
REJESTR_IO_BASE_API = "https://rejestr.io/api/v2"

async def make_rejestr_io_request(endpoint: str) -> dict[str, Any]:
    """
    Make an authenticated HTTP GET request to the rejestr.io API.
    
    This internal helper function handles HTTP communication with the rejestr.io API,
    including authentication and error handling. It automatically includes the API key
    from environment variables in the request headers.
    
    Args:
        endpoint: API endpoint path relative to REJESTR_IO_BASE_API (e.g., "org/0000012345")
                 Should not include leading slash as it's added automatically
    
    Returns:
        JSON response from the API parsed as a dictionary
    
    Raises:
        httpx.HTTPError: If the API request fails (network error, 4xx/5xx status codes)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REJESTR_IO_BASE_API}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_token_amount() -> str:
    """
    Retrieve current API token balance from rejestr.io account.
    
    This tool checks the account balance (in PLN) for the rejestr.io API.
    Some operations like retrieving financial statements in JSON format cost tokens,
    so this tool helps monitor available credits before making expensive requests.
    
    Returns:
        String containing the current token balance in PLN format (e.g., "100.50 PLN")
        or error message if the request fails
    
    Example usage:
        Before downloading financial statements, check if there are sufficient tokens
    """
    try:
        data = await make_rejestr_io_request("konto/stan")
        return f"{data} PLN"
    except httpx.HTTPError as e:
        return f"An error occurred: {e}"   


@mcp.tool()
async def get_company_info_using_nip(nip: str) -> dict[str, Any]:
    """
    Retrieve comprehensive company information using NIP (Tax Identification Number).
    
    NIP (Numer Identyfikacji Podatkowej) is a Polish tax identification number.
    This tool searches the rejestr.io database and returns detailed company data
    including KRS number, REGON, addresses, legal form, and other registry information.
    
    Args:
        nip: 10-digit tax identification number without any special characters
             (e.g., "1234567890", not "123-456-78-90")
             Must be a valid, properly formatted NIP number
    
    Returns:
        Dictionary containing company data including:
        - Basic information (name, legal form, status)
        - Registration numbers (KRS, REGON, NIP)
        - Addresses (headquarters, correspondence)
        - Capital information
        - Registration dates
        Returns dict with "error" key if request fails
    """
    try:
        data = await make_rejestr_io_request(f"org/nip/{nip}")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_company_info_using_krs(krs: str) -> dict[str, Any]:
    """
    Retrieve comprehensive company information using KRS (National Court Register) number.
    
    KRS (Krajowy Rejestr Sądowy) is the Polish National Court Register number.
    This is the primary identifier for companies registered in Poland.
    
    Args:
        krs: KRS number in format "0000012345" (10 digits with leading zeros)
             or "12345" (without leading zeros). Both formats are accepted.
             Example: "0000012345" or "12345"
    
    Returns:
        Dictionary containing comprehensive company data including:
        - Basic information (name, legal form, status)
        - Registration numbers (KRS, REGON, NIP)
        - Addresses (headquarters, correspondence)
        - Share capital information
        - Management and representative data
        - Registration and modification dates
        Returns dict with "error" key if request fails
    """
    try:
        data = await make_rejestr_io_request(f"org/{krs}")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_company_info_using_name(name: str) -> dict[str, Any]:
    """
    Search for companies by name in the rejestr.io database.
    
    This tool performs a search query using company name as the search term.
    The search supports partial matches and returns paginated results with companies
    matching the provided name pattern, sorted by relevance and capital.
    
    Args:
        name: Company name or partial name to search for (e.g., "Microsoft")
              Search is case-insensitive and supports partial matching
    
    Returns:
        Dictionary containing search results with the following structure:
        - liczba_wszystkich_wynikow (int): Total number of matching organizations
        - wyniki (list): List of organizations for current page, each including:
          * id (int): Organization ID (KRS number without leading zeros)
          * nazwy: Various name variants of the organization
          * numery: Registration numbers (KRS, NIP, REGON)
          * stan: Key data about organization status (active, liquidation, etc.)
          * adres: Main organization address from KRS
          * krs_wpisy: Information about key KRS entries
          * krs_powiazania_liczby: Number of connections with other entities
        Returns dict with "error" key if request fails
    
    Note:
        - This is a search endpoint returning paginated results (default 10 per page)
        - Results are sorted by text match relevance, modified by share capital
        - Additional search parameters (NIP, REGON, legal form, PKD codes, status flags,
          capital, size, location) are available in the API but not exposed in this tool
        - For exact company data after finding it, use get_company_info_using_krs
          or get_company_info_using_nip with the KRS/NIP from search results
    """
    try:
        data = await make_rejestr_io_request(f"org?nazwa={name}")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_company_krs_documentation(krs: str, chapter: str) -> dict[str, Any]:
    """
    Retrieve specific chapter of KRS (National Court Register) documentation for a company.
    
    The KRS register is organized into chapters (divisions), each containing specific
    types of information about the company. This tool retrieves data from a selected chapter.
    
    Args:
        krs: KRS number in format "0000012345" or "12345"
        chapter: One of the following valid chapter names:
                 - "ogolny" - General information (basic company data, purpose, representatives)
                 - "oddzialy" - Branches and organizational units
                 - "akcje" - Shares and shareholders information
                 - "wzmianki" - Mentions and annotations (bankruptcy, liquidation, etc.)
                 - "zobowiazania" - Liabilities and encumbrances
                 - "przeksztalcenia" - Transformations and organizational changes
    
    Returns:
        Dictionary containing the requested chapter data with detailed structured information
        specific to that chapter. Returns dict with "error" key if request fails or
        if invalid chapter name is provided.
    
    Important:
        Before calling this tool, verify that the user has selected a valid chapter name
        from the list above. Invalid chapter names will result in API errors.
    """
    try:
        data = await make_rejestr_io_request(f"org/{krs}/krs-rozdzialy/{chapter}")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_person_data(id: str) -> dict[str, Any]:
    """
    Retrieve detailed information about a person (individual) from the rejestr.io database.
    
    This tool fetches data about individuals registered in the business registry,
    typically company officers, board members, shareholders, or beneficiaries.
    The person ID must be obtained from other tools first.
    
    Args:
        id: Unique person identifier in the rejestr.io database
            This ID can be obtained from:
            - get_company_info_using_name() - from company structure data
            - get_company_info_using_nip() - from company structure data
            - get_company_info_using_krs() - from company structure data
            - get_beneficiary() - from beneficiary list
    
    Returns:
        Dictionary containing person data including:
        - Full name and personal details
        - PESEL (if available and public)
        - Addresses
        - Roles in companies
        - Related company connections
        Returns dict with "error" key if request fails
    
    Workflow:
        1. First, use company search tools to find the company
        2. Extract person IDs from the company data or beneficiary list
        3. Then use this tool with the extracted ID to get detailed person information
    
    Example:
        # First find a company and get person ID from its data
        company = await get_company_info_using_krs("0000012345")
        person_id = company['representatives'][0]['id']  # Example extraction
        
        # Then get detailed person data
        person_data = await get_person_data(person_id)
    """
    try:
        data = await make_rejestr_io_request(f"osoby/{id}")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_beneficiary(krs: str) -> list[dict[str, Any]]:
    """
    Retrieve list of real beneficiaries for a company from CRBR register.
    
    CRBR (Centralny Rejestr Beneficjentów Rzeczywistych) is the Central Register
    of Real Beneficiaries in Poland. This register contains information about individuals
    who ultimately own or control legal entities.
    
    Important: This data comes from CRBR, not from KRS. It shows real beneficial owners,
    which may differ from formal company representatives in KRS.
    
    Args:
        krs: KRS number of the company in format "0000012345" or "12345"
    
    Returns:
        List of dictionaries, each containing information about a beneficiary:
        - Personal data (name, PESEL if available)
        - Citizenship and residence
        - Nature of beneficial ownership (ownership %, voting rights, control)
        - Date of entry in the register
        Returns dict with "error" key if request fails or no beneficiaries found
    
    Note:
        Not all companies have entries in CRBR. Some companies may be exempt
        from reporting beneficiaries or may not have completed this requirement.
    
    Example:
        beneficiaries = await get_beneficiary("0000012345")
        if isinstance(beneficiaries, list):
            print(f"Found {len(beneficiaries)} beneficiaries")
    """
    try:
        data = await make_rejestr_io_request(f"org/{krs}/crbr")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_connections_by_krs(krs: str) -> list[dict[str, Any]]:
    """
    Retrieve all business connections and relationships for a company.
    
    This tool returns a comprehensive list of connections between the specified company
    and other entities (companies and individuals). Connections include various types
    of relationships such as ownership, management, representation, and other legal ties.
    
    Args:
        krs: KRS number of the company in format "0000012345" or "12345"
    
    Returns:
        List of dictionaries describing connections. Each connection includes:
        - Connected entity details (person or company)
        - Type of relationship (owner, board member, representative, etc.)
        - Role description
        - Dates of relationship (start, end if applicable)
        - Additional context about the connection
        Returns dict with "error" key if request fails
    
    Use cases:
        - Analyzing company ownership structure
        - Identifying key decision makers
        - Mapping business relationships
        - Due diligence and compliance checks
        - Understanding corporate governance
    
    Example:
        connections = await get_connections_by_krs("0000012345")
        if isinstance(connections, list):
            print(f"Found {len(connections)} connections")
    """
    try:
        data = await make_rejestr_io_request(f"org/{krs}/krs-powiazania")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_connections_by_person(id: str) -> list[dict[str, Any]]:
    """
    Retrieve all business connections and relationships for a specific person.
    
    This tool returns a comprehensive list of connections between the specified individual
    and companies/other entities. It shows all companies where the person has any role
    (owner, board member, proxy, shareholder, etc.) and other business relationships.
    
    Args:
        id: Unique person identifier in the rejestr.io database
            This ID must be obtained first from:
            - get_company_info_using_name() - from company structure data
            - get_company_info_using_nip() - from company structure data
            - get_company_info_using_krs() - from company structure data
            - get_beneficiary() - from beneficiary list
    
    Returns:
        List of dictionaries describing connections. Each connection includes:
        - Company details (name, KRS, status)
        - Person's role in the company
        - Dates of relationship (appointment, termination if applicable)
        - Additional context (powers, limitations, etc.)
        Returns dict with "error" key if request fails
    
    Use cases:
        - Finding all companies where a person is involved
        - Analyzing individual's business portfolio
        - Due diligence on key persons
        - Investigating business networks
        - Compliance and background checks
    """

    try:
        data = await make_rejestr_io_request(f"osoby/{id}/krs-powiazania")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_financial_documents(krs: str) -> list[dict[str, Any]]:
    """
    Retrieve list of all financial documents filed by a company in KRS.
    
    This tool returns metadata about financial documents that have been submitted
    to the National Court Register. These include annual financial statements,
    consolidated statements, audit reports, and other financial disclosures.
    
    Args:
        krs: KRS number of the company in format "0000012345" or "12345"
    
    Returns:
        List of dictionaries, each representing a financial document with metadata:
        - Document ID (needed to retrieve full document)
        - Document type (balance sheet, P&L statement, cash flow, etc.)
        - Reporting period (fiscal year)
        - Filing date
        - czy_ma_json (boolean) - indicates if document is available in JSON format
        - Document status
        Returns dict with "error" key if request fails
    
    Note:
        This tool only returns the LIST of documents with metadata.
        To get the actual financial data in JSON format, use get_financial_statement_in_json
        with the document ID from this list (only for documents where czy_ma_json = true).
    
    Use cases:
        - Finding available financial statements for analysis
        - Checking which years have reported financials
        - Identifying documents available in structured JSON format
        - Listing all financial disclosures
    """
    try:
        data = await make_rejestr_io_request(f"org/{krs}/krs-dokumenty")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

@mcp.tool()
async def get_financial_statement_in_json(krs: str, doc_id: str) -> dict[str, Any]:
    """
    Retrieve full financial statement in structured JSON format.
    
    IMPORTANT: This operation costs 0.50 PLN per document request.
    Always inform the user about the cost and get confirmation before proceeding.
    Check available token balance using get_token_amount() before making the request.
    
    This tool downloads the complete financial statement data in a structured,
    machine-readable JSON format. The data includes detailed balance sheet items,
    profit and loss statement, cash flows, and other financial information.
    
    Args:
        krs: KRS number of the company in format "0000012345" or "12345"
        doc_id: Document identifier obtained from get_financial_documents() tool
                Only use documents where czy_ma_json = true
    
    Returns:
        Dictionary containing structured financial data:
        - Balance sheet (assets, liabilities, equity)
        - Profit and loss statement (revenues, expenses, net result)
        - Cash flow statement (operating, investing, financing activities)
        - Notes and additional information
        - Reporting period and company details
        Returns dict with "error" key if request fails
    
    Workflow (REQUIRED):
        1. Check token balance: await get_token_amount()
        2. Get document list: await get_financial_documents(krs)
        3. Find document with czy_ma_json = true
        4. Inform user about 0.50 PLN cost and get confirmation
        5. Use this tool with the doc_id from step 2
    """
    try:
        data = await make_rejestr_io_request(f"org/{krs}/krs-dokumenty/{doc_id}?format=json")
        return data
    except httpx.HTTPError as e:
        return {"error": f"An error occurred: {e}"}

def main():
    """
    Entry point for the MCP server.
    
    Initializes and runs the FastMCP server using stdio transport,
    enabling communication with MCP clients (such as Claude Desktop).
    """
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()