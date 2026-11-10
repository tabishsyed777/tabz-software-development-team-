from tools.git_tools import secret_scan
def prepare(root):
    findings = secret_scan(root)
    return {"ready": not findings, "secret_findings": findings, "linkedin_draft": "Built a project with Tabz Software Development Team—spec-first, test-first, and approval-gated."}
