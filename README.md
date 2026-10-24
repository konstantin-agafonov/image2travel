# Image2Travel

MCP server that turns photos into realistic travel plans preserving the impression.

## Quick start

```bash
uv sync
uv run python -m image2travel --transport stdio
```

## Environment
- `IMAGE2TRAVEL_DATA_DIR` - data directory (default: ./data)

## Tools
- `plan_trip` - get destination concepts
- `get_destination` - get destination details
- `build_itinerary` - build itinerary
- `validate_itinerary` - validate feasibility
- `verify_place` - verify place
- `export_itinerary` - export to file
