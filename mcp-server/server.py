from fastmcp import FastMCP

from attendance_api import (
    get_pending_attendance,
    bulk_approve,
)

mcp = FastMCP("AI Attendance MCP")


@mcp.tool()
def pending_attendance():

    """
    Show pending attendance records.
    """

    return get_pending_attendance()


@mcp.tool()
def approve_except(exclude_names: list[str]):

    """
    Bulk approve attendance except specified employee names.
    """

    return bulk_approve(exclude_names)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8001
    )