from pathlib import Path

p = Path("app.py")
text = p.read_text()

# JSON error blocks, e.g. {"error": format_limit_error(e)}
text = text.replace(
'''            "error": format_limit_error(e)
''',
'''            "error": format_limit_error(e),
            "code": "limit_reached",
            "lock": True
'''
)

# SSE image/tool fatal error blocks, e.g. {"message": format_limit_error(e)}
text = text.replace(
'''                        "message": format_limit_error(e)
''',
'''                        "message": format_limit_error(e),
                        "code": "limit_reached",
                        "lock": True
'''
)

p.write_text(text)
print("✅ app.py limit errors now include code + lock")
