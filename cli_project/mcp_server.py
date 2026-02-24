from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc",
    description="Read the contents of a document. Input is the name of the document.",
)
def read_doc(doc_name: str) -> str:
    return docs.get(doc_name, "Document not found.")

@mcp.tool(
    name="edit_doc",
    description="Edit a document by replacing a string in its content. Input is the name of the document, the string to replace, and the new content.",
)
def edit_doc(doc_name: str, old_string: str, new_content: str):
    if doc_name in docs:
        old_content = docs[doc_name]
        if old_string in old_content:
            docs[doc_name] = old_content.replace(old_string, new_content)
        else:
            raise ValueError(f"String '{old_string}' not found in document '{doc_name}'.")
    else:
        raise ValueError(f"Document '{doc_name}' not found.")

@mcp.resource(
    name="list_docs", 
    description="Return a list of all document names.", 
    uri="docs://documents",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    return list(docs.keys())

@mcp.resource(
    name="get_doc", 
    description="Return the contents of a specific document.",
    uri="docs://documents/{doc_name}",
    mime_type="text/plain"
)
def get_doc(doc_name: str) -> str:
    content = docs.get(doc_name, "Document not found.")
    if content == "Document not found.":
        raise ValueError(f"Document '{doc_name}' not found.")
    return content

# TODO: Write a prompt to rewrite a doc in markdown format
# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")
