# Tostada Templates

## Overview

The `templates/` directory contains HTML templates used by Tostada to generate dynamic HTTP responses.

Templates separate page presentation from request-handling logic. An action can pass data to a template, which combines HTML markup with embedded Python code to generate the final response.

## How Templates Work

Templates are processed by the `HTTPHandler` class in `my_http_handler.py`.

An action invokes a template using `execute_template()`:

```python
parameters["title"] = "Welcome to Tostada"
parameters["username"] = "Developer"

self.execute_template("/example.html", parameters)
```

The template path is relative to the configured templates directory. The `parameters` dictionary provides values that the template can use when generating its output.

## HTML and Embedded Python

Tostada supports embedded Python blocks within HTML templates using `<%` and `%>` delimiters.

For example, the following template generates an HTML page using values supplied by an action.

**`example.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><%= parameters["title"] %></title>
</head>
<body>
    <header>
        <h1><%= parameters["title"] %></h1>
    </header>

    <main>
        <p>Welcome, <%= parameters["username"] %>!</p>

        <%
        for number in range(1, 4):
            template_print(f"<p>Generated item {number}</p>")
        %>
    </main>
</body>
</html>
```

In this example:

- `<%= ... %>` evaluates a Python expression and inserts its result into the template output.
- `<% ... %>` executes a Python code block.
- `template_print()` writes generated content into the rendered template.

The example demonstrates how a single template can combine ordinary HTML, dynamic values, and Python-controlled output.

## Directory Structure

Templates can be organized according to the application they support.

```text
web/
└── templates/
    ├── example.html
    ├── dashboard.html
    └── error.html
```

These filenames are illustrative. Applications define their own templates based on their requirements.

## Configuration

The templates directory is configured in `Server_Config/http_config.json` under the `paths.templates` setting. Its location is resolved relative to the configured framework root path.

## Developer Notes

- Invoke templates from application actions using `self.execute_template(path, parameters)`.
- Keep reusable presentation markup in templates instead of duplicating it across actions.
- Embedded Python is executable code; templates should be treated as trusted application code.
- Escape untrusted values before inserting them into HTML to prevent HTML injection and cross-site scripting.
- Keep application-specific templates separate from the reusable HTTP server implementation.

Tostada provides the template-processing mechanism, while the application developer defines the page structure and behavior.
