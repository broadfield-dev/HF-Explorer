# Huggingface File Explorer Component
![image](hf_explorer.png "Title")


A custom Gradio component that provides a powerful file explorer and environment inspector. It can be easily embedded into any Gradio application to allow users to:

- Navigate the local file system (Linux).
- View and inspect file contents.
- Check installed Python dependencies (`pip freeze`).
- View system disk usage (`df -h`).

This component is particularly useful for debugging and inspecting environments in services like Hugging Face Spaces.

 <!-- It's a good idea to add a screenshot -->

## Installation

You can install this component directly from GitHub:

```bash
pip install git+https://github.com/broadfield-dev/hf-explorer.git
```

## Usage

Using the `FileExplorer` is as simple as importing it and instantiating it within a `gr.Blocks` app.

```python
import gradio as gr
from gradio_file_explorer import FileExplorer

with gr.Blocks() as demo:
    gr.Markdown("## My App with a Built-in File Explorer")

    # Simply instantiate the component
    FileExplorer()

    gr.Textbox(label="Other components can coexist seamlessly.")

demo.launch()
```

## Customization

You can customize the initial paths when creating an instance of the `FileExplorer`:

```python
FileExplorer(
    root_path="/",                 # The top-level directory user can access
    app_path="/app",               # The "Home" button destination
    glob="*.py"                    # Only show python files
)
```

## System Dependencies

This component uses the following command-line tools for full functionality. They are typically pre-installed on Linux and macOS systems (like Hugging Face Spaces).

- `file`: To determine the MIME type of a file and avoid displaying binary content.
- `df`: To display disk usage information.

The component will still function without them, but with reduced capabilities.
