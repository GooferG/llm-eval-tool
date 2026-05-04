"""Mock tool implementations + their JSON schemas.

The schemas are passed to the model so it knows what tools exist.
The execute() function runs the call and returns canned data.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_capital",
            "description": "Get the capital city of a country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name, e.g. 'France'"},
                },
                "required": ["country"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_population",
            "description": "Get the population of a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
                },
                "required": ["city"],
            },
        },
    },
]


def execute(name, args):
    if name == "get_weather":
        city = args.get("city", "")
        data = {
            "Paris": {"temp_c": 18, "condition": "cloudy"},
            "London": {"temp_c": 12, "condition": "rain"},
            "Tokyo": {"temp_c": 22, "condition": "clear"},
        }
        return data.get(city, {"error": f"unknown city: {city}"})

    if name == "get_capital":
        data = {"France": "Paris", "Japan": "Tokyo", "Brazil": "Brasilia"}
        return {"capital": data.get(args.get("country", ""), "unknown")}

    if name == "get_population":
        data = {"Paris": 2_161_000, "Tokyo": 13_960_000, "Brasilia": 3_055_000}
        return {"population": data.get(args.get("city", ""), 0)}

    return {"error": f"unknown tool: {name}"}
